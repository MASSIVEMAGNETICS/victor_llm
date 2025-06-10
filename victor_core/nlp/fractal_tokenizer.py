import re
import math
import hashlib
import asyncio # For pulse publishing

from victor_core.logger import VictorLoggerStub
# Assuming BrainFractalPulseExchange will be passed during instantiation
# from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange

logger = VictorLoggerStub(component="FractalTokenKernel")

class FractalTokenKernel_v1_1_0:
    def __init__(self, pulse_exchange=None, config=None):
        self.pulse = pulse_exchange # Instance of BrainFractalPulseExchange
        self.config = config # Instance of ASIConfigCore or similar
        self.vocabulary = {}
        self.reverse_vocabulary = {}
        self.token_counts = {}
        self.next_token_id = 0
        logger.info("FractalTokenKernel_v1_1_0 initialized.")
        # Example: Use a config value if available
        # self.max_keywords = self.config.MAX_TOKENIZER_KEYWORDS if self.config else 3

    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with single
        text = re.sub(r'[^\w\s\.\-\']', '', text) # Keep alphanumeric, spaces, periods, hyphens, apostrophes
        return text.strip()

    def train(self, text_corpus: list[str]):
        logger.info(f"Starting training on a corpus of {len(text_corpus)} documents.")
        for text in text_corpus:
            normalized_text = self._normalize_text(text)
            words = normalized_text.split()
            for word in words:
                if word not in self.vocabulary:
                    self.vocabulary[word] = self.next_token_id
                    self.reverse_vocabulary[self.next_token_id] = word
                    self.token_counts[word] = 0
                    self.next_token_id += 1
                self.token_counts[word] += 1
        logger.info(f"Training complete. Vocabulary size: {len(self.vocabulary)}")
        if self.pulse:
            asyncio.create_task(self.pulse.publish("tokenizer_train_complete", {"vocab_size": len(self.vocabulary)}))


    def tokenize(self, text: str) -> list[int]:
        normalized_text = self._normalize_text(text)
        words = normalized_text.split()
        tokens = [self.vocabulary.get(word, -1) for word in words] # -1 for OOV (Out Of Vocabulary)

        # Simple keyword extraction based on frequency (example)
        # More sophisticated methods would involve TF-IDF, embeddings, etc.
        keywords = []
        if self.config and hasattr(self.config, 'MAX_TOKENIZER_KEYWORDS'):
            max_keywords = self.config.MAX_TOKENIZER_KEYWORDS
            word_counts_in_text = {word: words.count(word) for word in set(words) if word in self.vocabulary}
            # Sort words by their overall frequency in the training corpus (desc) then by count in text
            sorted_words = sorted(word_counts_in_text.keys(),
                                  key=lambda w: (self.token_counts.get(w, 0), word_counts_in_text[w]),
                                  reverse=True)
            keywords = sorted_words[:max_keywords]

        if self.pulse:
            asyncio.create_task(self.pulse.publish(
                "text_tokenized",
                {"text_length": len(words), "token_count": len(tokens), "keywords_extracted": keywords}
            ))
        return tokens

    def detokenize(self, tokens: list[int]) -> str:
        words = [self.reverse_vocabulary.get(token, "<UNK>") for token in tokens]
        return " ".join(words)

    def get_keyword_hashes(self, text: str, num_keywords: int = 3) -> list[str]:
        """
        Extracts keywords, generates their hashes.
        A more complex version would use TF-IDF or other measures.
        This is a simplified version.
        """
        normalized_text = self._normalize_text(text)
        words = list(set(normalized_text.split())) # Unique words in text

        # Sort words by general frequency (if available) or just take first N for simplicity
        # This is a placeholder for a real keyword extraction logic
        if not self.token_counts: # If not trained, cannot sort by frequency
            keywords = words[:num_keywords]
        else:
            # Sort by frequency in descending order
            keywords = sorted(words, key=lambda word: self.token_counts.get(word, 0), reverse=True)
            keywords = [kw for kw in keywords if kw in self.vocabulary][:num_keywords] # Filter by vocab

        keyword_hashes = []
        for keyword in keywords:
            # Create a simple hash (MD5 for consistency, could be others)
            hasher = hashlib.md5()
            hasher.update(keyword.encode('utf-8'))
            keyword_hashes.append(hasher.hexdigest()[:16]) # Truncate for brevity

        if self.pulse:
             asyncio.create_task(self.pulse.publish("keywords_hashed", {"text_snippet": text[:50], "num_keywords": len(keyword_hashes)}))
        return keyword_hashes

    def calculate_fractal_dimension(self, text: str) -> float:
        """
        Placeholder for a more complex fractal dimension calculation.
        This simplified version uses vocabulary richness (Type-Token Ratio).
        """
        normalized_text = self._normalize_text(text)
        words = normalized_text.split()
        if not words:
            return 0.0

        num_types = len(set(words))
        num_tokens = len(words)
        ttr = num_types / num_tokens if num_tokens > 0 else 0

        # Simple transformation to a "fractal-like" value, not a true fractal dimension
        fractal_value = math.log1p(num_types) / math.log1p(num_tokens) if num_tokens > 0 else 0

        if self.pulse:
            asyncio.create_task(self.pulse.publish("fractal_dimension_calculated", {"text_snippet": text[:50], "dimension": fractal_value}))
        return fractal_value

# Example Usage (assuming pulse_exchange and config are available)
async def tokenizer_main_example():
    from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
    from victor_core.config import ASIConfigCore

    config_instance = ASIConfigCore()
    pulse_exchange_instance = BrainFractalPulseExchange()
    await pulse_exchange_instance.start_pulse()

    tokenizer = FractalTokenKernel_v1_1_0(pulse_exchange=pulse_exchange_instance, config=config_instance)

    corpus = [
        "This is the first document.",
        "This document is the second document.",
        "And this is the third one.",
        "Is this the first document?",
    ]
    tokenizer.train(corpus)

    test_text = "This is a test document about the first and second."
    tokens = tokenizer.tokenize(test_text)
    logger.info(f"Tokens for '{test_text}': {tokens}")

    detokenized_text = tokenizer.detokenize(tokens)
    logger.info(f"Detokenized text: {detokenized_text}")

    hashes = tokenizer.get_keyword_hashes(test_text, num_keywords=config_instance.MAX_TOKENIZER_KEYWORDS)
    logger.info(f"Keyword hashes for '{test_text}': {hashes}")

    dimension = tokenizer.calculate_fractal_dimension(test_text)
    logger.info(f"Fractal dimension for '{test_text}': {dimension}")

    await asyncio.sleep(0.1) # allow time for async logs if any
    await pulse_exchange_instance.stop_pulse()

if __name__ == "__main__":
    # To run this example, you might need to adjust logger verbosity for demo
    # logger.log_level_str = "DEBUG"
    # logger.current_log_level_int = logger.log_levels_map.get(logger.log_level_str, 2)
    asyncio.run(tokenizer_main_example())
