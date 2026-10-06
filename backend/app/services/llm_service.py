"""LLM inference service implementation for local models (e.g., Qwen2.5)."""

from abc import ABC, abstractmethod
import threading
from typing import Any, List, Optional
import torch

from app.core.config import settings
from app.core.exceptions import LLMException
from app.core.logging import logger

SYSTEM_PROMPT = (
    "You are an expert academic research assistant. Answer the user's question using ONLY "
    "the provided academic document context excerpts.\n\n"
    "Strict Academic Grounding Rules:\n"
    "1. Answer strictly using only supplied document context. Do not use outside knowledge.\n"
    "2. If the provided context is insufficient to answer the question, explicitly reply: "
    '"The provided academic documents do not contain enough information to answer this question."\n'
    "3. Do not fabricate citations, page numbers, author names, statistics, datasets, or methodology details.\n"
    "4. Cite every factual claim using bracketed labels corresponding to the sources provided, e.g. [Source 1], [Source 2].\n"
    "5. Clearly distinguish between explicitly stated facts and reasonable interpretations. Prefer phrases like \"The provided excerpts indicate...\" over unsupported certainty.\n"
    "6. If retrieved sources contain conflicting evidence or disagreements, explicitly state them.\n"
    "7. For comparisons across documents, clearly identify the specific documents or paper titles.\n"
    "8. Maintain technical precision, academic rigor, and concise clarity."
)


def build_research_mode_instructions(mode: Optional[str]) -> str:
    """Build research mode-specific prompt instructions."""
    mode_str = (mode or "qa").lower().strip()
    if mode_str == "summary":
        return (
            "RESEARCH MODE: SUMMARY\n"
            "Structure your response around: Research Objective, Approach, Main Findings, Conclusions, and Important Limitations.\n"
            "Only include information directly supported by the supplied document context excerpts."
        )
    elif mode_str == "methodology":
        return (
            "RESEARCH MODE: METHODOLOGY\n"
            "Focus on: Research design, Dataset/sample, Data collection, Preprocessing, Methods, Models/algorithms, Experimental setup, Evaluation, and Statistical methods.\n"
            "Do not invent methodological details not present in the context."
        )
    elif mode_str == "findings":
        return (
            "RESEARCH MODE: FINDINGS\n"
            "Focus on: Primary findings, Secondary findings, Quantitative results, Qualitative results, Evidence, and Implications stated by the authors.\n"
            "Distinguish explicitly stated findings from reasonable interpretations."
        )
    elif mode_str == "limitations":
        return (
            "RESEARCH MODE: LIMITATIONS\n"
            "Focus on: Explicitly stated limitations, Potential limitations supported by evidence, Scope limitations, Dataset limitations, Methodological limitations, and Evaluation limitations.\n"
            "Clearly label inferred limitations as interpretations. Never present an inferred limitation as explicitly stated."
        )
    elif mode_str == "compare":
        return (
            "RESEARCH MODE: COMPARE\n"
            "Focus on: Similarities, Differences, Methodology, Datasets, Models, Experimental setup, Findings, Limitations, and Contradictions.\n"
            "Use document titles or IDs so the user can clearly identify which source is being discussed. Do not fabricate differences. If retrieved context lacks comparison evidence, state that explicitly."
        )
    else:  # qa or default
        return (
            "RESEARCH MODE: QUESTION ANSWERING (QA)\n"
            "Focus on directly answering the question with evidence, concise explanations, and citations."
        )


class BaseLLMService(ABC):
    """Abstract interface for LLM model inference."""

    @abstractmethod
    async def generate_answer(
        self,
        prompt: str,
        context: str,
        conversation_history: Optional[List[Any]] = None,
        research_mode: str = "qa",
    ) -> str:
        """Generate grounded answer from context prompt using LLM."""
        raise NotImplementedError


class LocalLLMService(BaseLLMService):
    """Concrete local LLM implementation using Hugging Face Transformers (e.g. Qwen2.5)."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        self.model_name = model_name or settings.LLM_MODEL
        self.device_setting = device or settings.LLM_DEVICE
        self.max_new_tokens = max_new_tokens or settings.LLM_MAX_NEW_TOKENS
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self._model = None
        self._tokenizer = None
        self._device = None

    def _resolve_device(self) -> str:
        if self.device_setting.lower() == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.device_setting

    def _load_model(self):
        """Lazily load tokenizer and model onto specified device."""
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading local LLM model '{self.model_name}'...")
            self._device = self._resolve_device()
            logger.info(f"Using device '{self._device}' for LLM inference.")

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )
            model_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": False if self._device == "cpu" else True,
            }
            if self._device == "cuda":
                model_kwargs["torch_dtype"] = torch.float16

            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs,
            )

            self._model.to(self._device)
            self._model.eval()
            logger.info(f"Successfully loaded LLM model '{self.model_name}'.")

        except Exception as e:
            logger.error(f"Failed to load LLM model '{self.model_name}': {str(e)}")
            raise LLMException(
                message=f"Failed to load LLM model '{self.model_name}': {str(e)}",
                details={"model_name": self.model_name, "error": str(e)},
            )

    def _prepare_messages(
        self,
        prompt: str,
        context: str,
        conversation_history: Optional[List[Any]] = None,
        research_mode: str = "qa",
    ) -> List[dict]:
        """Construct prompt messages array for chat format including research mode and history."""
        mode_instruction = build_research_mode_instructions(research_mode)
        system_content = f"{SYSTEM_PROMPT}\n\n{mode_instruction}"
        messages = [{"role": "system", "content": system_content}]

        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                else:
                    role = getattr(msg, "role", "user")
                    role = role.value if hasattr(role, "value") else str(role)
                    content = getattr(msg, "content", "")
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"})
        return messages

    async def generate_answer(
        self,
        prompt: str,
        context: str,
        conversation_history: Optional[List[Any]] = None,
        research_mode: str = "qa",
    ) -> str:
        """Generate grounded answer from context prompt using LLM."""
        if not prompt or not prompt.strip():
            raise LLMException("Prompt cannot be empty.")

        try:
            self._load_model()

            messages = self._prepare_messages(
                prompt=prompt,
                context=context,
                conversation_history=conversation_history,
                research_mode=research_mode,
            )

            if hasattr(self._tokenizer, "apply_chat_template"):
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                mode_inst = build_research_mode_instructions(research_mode)
                formatted_prompt = (
                    f"System: {SYSTEM_PROMPT}\n\n{mode_inst}\n\nContext:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"
                )

            inputs = self._tokenizer(formatted_prompt, return_tensors="pt")
            if hasattr(inputs, "to"):
                inputs = inputs.to(self._device)
            elif isinstance(inputs, dict):
                inputs = {k: (v.to(self._device) if hasattr(v, "to") else v) for k, v in inputs.items()}
            input_ids_length = inputs["input_ids"].shape[1]

            do_sample = self.temperature > 0.0
            gen_kwargs = {
                "max_new_tokens": self.max_new_tokens,
                "do_sample": do_sample,
                "pad_token_id": self._tokenizer.eos_token_id,
            }
            if do_sample:
                gen_kwargs["temperature"] = self.temperature

            with torch.no_grad():
                output_tokens = self._model.generate(**inputs, **gen_kwargs)

            generated_tokens = output_tokens[0][input_ids_length:]
            answer = self._tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

            if not answer:
                answer = "The provided academic documents do not contain enough information to answer this question."

            return answer

        except LLMException:
            raise
        except Exception as e:
            logger.error(f"LLM generation failure: {str(e)}")
            raise LLMException(
                message=f"LLM generation failed: {str(e)}",
                details={"error": str(e)},
            )

    async def generate_answer_stream(
        self,
        prompt: str,
        context: str,
        conversation_history: Optional[List[Any]] = None,
        research_mode: str = "qa",
    ):
        """Yield generated token text chunks as they are produced by the LLM."""
        if not prompt or not prompt.strip():
            raise LLMException("Prompt cannot be empty.")

        try:
            self._load_model()

            messages = self._prepare_messages(
                prompt=prompt,
                context=context,
                conversation_history=conversation_history,
                research_mode=research_mode,
            )

            if hasattr(self._tokenizer, "apply_chat_template"):
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                mode_inst = build_research_mode_instructions(research_mode)
                formatted_prompt = (
                    f"System: {SYSTEM_PROMPT}\n\n{mode_inst}\n\nContext:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"
                )

            inputs = self._tokenizer(formatted_prompt, return_tensors="pt")
            if hasattr(inputs, "to"):
                inputs = inputs.to(self._device)
            elif isinstance(inputs, dict):
                inputs = {k: (v.to(self._device) if hasattr(v, "to") else v) for k, v in inputs.items()}

            from transformers import TextIteratorStreamer

            streamer = TextIteratorStreamer(self._tokenizer, skip_prompt=True, skip_special_tokens=True)
            do_sample = self.temperature > 0.0
            gen_kwargs = {
                **inputs,
                "streamer": streamer,
                "max_new_tokens": self.max_new_tokens,
                "do_sample": do_sample,
                "pad_token_id": self._tokenizer.eos_token_id,
            }
            if do_sample:
                gen_kwargs["temperature"] = self.temperature

            thread = threading.Thread(target=self._model.generate, kwargs=gen_kwargs)
            thread.start()

            for new_text in streamer:
                yield new_text

        except LLMException:
            raise
        except Exception as e:
            logger.error(f"LLM streaming generation failure: {str(e)}")
            raise LLMException(
                message=f"LLM streaming generation failed: {str(e)}",
                details={"error": str(e)},
            )


# Global service instance with lazy model loading
llm_service = LocalLLMService()
