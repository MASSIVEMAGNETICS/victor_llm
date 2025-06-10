import json
import hashlib
import datetime
import threading
import numpy as np
import math
import time # Added for decay calculation example

from victor_core.logger import VictorLoggerStub
from victor_core.config import ASIConfigCore
# No CONFIG instance here, will use ASIConfigCore class variables directly or passed config

class HyperFractalMemory:
    def __init__(self, storage_path="bando_agi_persistent/hyper_fractal_memory.json", config=None):
        self.storage_path = storage_path
        self.config = config if config else ASIConfigCore() # Use passed config or default
        self.logger = VictorLoggerStub(component="HyperFractalMemory")
        self.memory_bank = {} # Stores memory entries: {content_hash: entry}
        self.semantic_index = {} # Example: {keyword_hash: [content_hash_1, content_hash_2]}
        self.temporal_index = {} # Example: {timestamp_bin: [content_hash_1]}
        self._lock = threading.Lock()
        self._load_memory()
        self.logger.info(f"HyperFractalMemory initialized. Loaded {len(self.memory_bank)} entries.")

    def _generate_content_hash(self, content_data: dict) -> str:
        """Generates a SHA256 hash for the structured content."""
        # Ensure consistent hashing by sorting keys
        serialized_content = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(serialized_content.encode('utf-8')).hexdigest()

    def _get_timestamp_bin(self, timestamp: datetime.datetime, precision="hour") -> str:
        """Bins timestamps for temporal indexing."""
        if precision == "hour":
            return timestamp.strftime("%Y-%m-%dT%H:00:00")
        elif precision == "day":
            return timestamp.strftime("%Y-%m-%d")
        else: # Default to minute precision
            return timestamp.strftime("%Y-%m-%dT%H:%M:00")

    def _calculate_emotional_impact(self, emotional_tags: dict) -> float:
        """Calculates a scalar emotional impact score from tags."""
        # Example: sum of absolute values of emotional scores
        if not emotional_tags or not isinstance(emotional_tags, dict):
            return 0.0
        return sum(abs(v) for v in emotional_tags.values() if isinstance(v, (int, float)))

    def _calculate_relevance_decay(self, entry_timestamp: datetime.datetime, current_time: datetime.datetime) -> float:
        """Calculates decay factor based on age. More sophisticated decay needed."""
        age_seconds = (current_time - entry_timestamp).total_seconds()
        # Example decay: half-life of 1 day (86400 seconds)
        # This is a very basic model. A proper model would use config parameters.
        half_life_seconds = 86400
        decay_factor = math.exp(-math.log(2) * age_seconds / half_life_seconds)
        return decay_factor


    def store_memory_entry(self, content_data: dict, text_summary: str,
                           vector_embedding: np.ndarray = None,
                           keyword_hashes: list[str] = None,
                           emotional_tags: dict = None,
                           related_memory_hashes: list[str] = None):
        with self._lock:
            content_hash = self._generate_content_hash(content_data)
            if content_hash in self.memory_bank:
                self.logger.debug(f"Memory entry {content_hash} already exists. Updating metadata.")
                # Potentially update timestamp or increment access count here
                self.memory_bank[content_hash]['last_accessed_ts'] = datetime.datetime.utcnow()
                self.memory_bank[content_hash]['access_count'] +=1
                return content_hash

            timestamp = datetime.datetime.utcnow()
            emotional_impact = self._calculate_emotional_impact(emotional_tags)

            # Determine if memory is significant enough to be stored long-term based on initial impact
            # MIN_EMOTIONAL_RELEVANCE is used here from config
            if emotional_impact < self.config.MIN_EMOTIONAL_RELEVANCE:
                 self.logger.debug(f"Memory entry for '{text_summary[:30]}...' below emotional relevance threshold. Not stored permanently yet.")
                 # Could store in a temporary buffer or simply not add to main bank yet
                 # For this example, we'll add it but it might be pruned aggressively

            entry = {
                "content_hash": content_hash,
                "content_data": content_data, # The actual detailed information
                "text_summary": text_summary, # Human-readable summary
                "vector_embedding": vector_embedding.tolist() if vector_embedding is not None else None,
                "keyword_hashes": keyword_hashes if keyword_hashes else [],
                "emotional_tags": emotional_tags if emotional_tags else {},
                "emotional_impact_score": emotional_impact,
                "related_memory_hashes": related_memory_hashes if related_memory_hashes else [],
                "creation_ts": timestamp,
                "last_accessed_ts": timestamp,
                "access_count": 1,
                "relevance_score": emotional_impact # Initial relevance, can be updated
            }
            self.memory_bank[content_hash] = entry

            # Update indices
            if keyword_hashes:
                for khash in keyword_hashes:
                    if khash not in self.semantic_index: self.semantic_index[khash] = []
                    self.semantic_index[khash].append(content_hash)

            time_bin = self._get_timestamp_bin(timestamp)
            if time_bin not in self.temporal_index: self.temporal_index[time_bin] = []
            self.temporal_index[time_bin].append(content_hash)

            self.logger.info(f"Stored new memory entry {content_hash} for: {text_summary[:50]}")
            self._save_memory() # Persist after important change
            return content_hash

    def retrieve_memory_by_hash(self, content_hash: str) -> dict | None:
        with self._lock:
            entry = self.memory_bank.get(content_hash)
            if entry:
                entry['last_accessed_ts'] = datetime.datetime.utcnow()
                entry['access_count'] += 1
                # Potentially re-calculate relevance here or during a maintenance cycle
                self.logger.debug(f"Retrieved memory entry {content_hash}")
                return entry.copy() # Return a copy to prevent modification
            self.logger.warn(f"Memory entry {content_hash} not found.")
            return None

    def search_memories(self, query_vector: np.ndarray = None, keyword_hashes: list[str] = None,
                        date_range: tuple[datetime.datetime, datetime.datetime] = None,
                        min_relevance: float = 0.1, top_n: int = 5) -> list[dict]:
        with self._lock:
            candidate_hashes = set()

            if keyword_hashes:
                for khash in keyword_hashes:
                    candidate_hashes.update(self.semantic_index.get(khash, []))

            # If no keyword matches, consider all memories (or implement vector-only search properly)
            # This part needs careful thought: if only vector is provided, how to get initial candidates?
            # For now, if keyword_hashes is empty or yields no results, we might have to iterate all.
            # This is inefficient. A proper vector index (FAISS, Annoy) is needed for pure vector search.

            # For simplicity, if vector is present and no keyword candidates, this search won't be effective
            # without iterating all. Let's assume for now keywords provide a first filter.
            # If candidate_hashes is empty after keyword search AND query_vector is present,
            # this indicates a need for a full scan or a vector index.

            retrieved_entries = []
            current_time = datetime.datetime.utcnow()

            for c_hash in list(candidate_hashes): # Iterate over a copy if modifying inside loop (not here)
                entry = self.memory_bank.get(c_hash)
                if not entry: continue

                # Temporal filter
                if date_range:
                    entry_ts = entry['creation_ts']
                    if not (date_range[0] <= entry_ts <= date_range[1]):
                        continue

                # Update relevance score based on decay and access, could be more complex
                # MEMORY_RETENTION_THRESHOLD is used here
                decay = self._calculate_relevance_decay(entry['creation_ts'], current_time)
                current_relevance = (entry.get('emotional_impact_score',0.1) + math.log1p(entry.get('access_count',1))) * decay
                entry['current_relevance_for_search'] = current_relevance # Temporary for sorting

                if current_relevance < self.config.MEMORY_RETENTION_THRESHOLD: # Pruning / ignoring low relevance
                    # self.logger.debug(f"Entry {c_hash} below retention threshold during search.")
                    continue

                if query_vector is not None and entry.get('vector_embedding') is not None:
                    entry_vec = np.array(entry['vector_embedding'])
                    # Cosine similarity, ensure query_vector and entry_vec are 1D
                    similarity = np.dot(query_vector, entry_vec) / (np.linalg.norm(query_vector) * np.linalg.norm(entry_vec))
                    entry['similarity_score'] = similarity # Store for ranking
                    # Could combine similarity with relevance: e.g. weight_sim * sim + weight_rel * rel
                    # For now, let's say relevance is a filter, similarity is for ranking
                    if similarity < min_relevance: # Assuming min_relevance applies to similarity here
                        continue
                elif query_vector is not None: # Query has vector, but entry doesn't
                    continue # Cannot compare

                retrieved_entries.append(entry)

            # Sort results: by similarity if available, otherwise by relevance
            # More sophisticated ranking would combine multiple factors
            def sort_key(e):
                sim = e.get('similarity_score', -1)
                rel = e.get('current_relevance_for_search', 0)
                # Prioritize similarity, then relevance. If no similarity, relevance is primary.
                return (sim, rel) if query_vector is not None else (rel, sim)

            retrieved_entries.sort(key=sort_key, reverse=True)
            self.logger.info(f"Search returned {len(retrieved_entries)} entries, taking top {top_n}.")
            return [e.copy() for e in retrieved_entries[:top_n]]


    def _save_memory(self):
        with self._lock:
            try:
                # Need to make datetime objects JSON serializable
                mem_bank_serializable = {}
                for hash_id, entry_data in self.memory_bank.items():
                    serializable_entry = entry_data.copy()
                    serializable_entry['creation_ts'] = entry_data['creation_ts'].isoformat()
                    serializable_entry['last_accessed_ts'] = entry_data['last_accessed_ts'].isoformat()
                    mem_bank_serializable[hash_id] = serializable_entry

                # Indexes are typically rebuilt on load or are simple enough
                # For this example, we only save the main bank.
                # A more robust system would save indexes or have a strategy for them.
                with open(self.storage_path, 'w') as f:
                    json.dump({"memory_bank": mem_bank_serializable}, f, indent=4)
                self.logger.debug(f"Memory saved to {self.storage_path}")
            except Exception as e:
                self.logger.error(f"Failed to save memory: {e}", exc_info=True)

    def _load_memory(self):
        with self._lock:
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    loaded_bank = data.get("memory_bank", {})
                    self.memory_bank = {}
                    for hash_id, entry_data in loaded_bank.items():
                        deserialized_entry = entry_data.copy()
                        deserialized_entry['creation_ts'] = datetime.datetime.fromisoformat(entry_data['creation_ts'])
                        deserialized_entry['last_accessed_ts'] = datetime.datetime.fromisoformat(entry_data['last_accessed_ts'])
                        # Ensure numpy arrays are restored if they were stored (they are lists in JSON)
                        if deserialized_entry.get('vector_embedding') is not None:
                            deserialized_entry['vector_embedding'] = np.array(deserialized_entry['vector_embedding'])
                        self.memory_bank[hash_id] = deserialized_entry

                # Rebuild indexes (simple version)
                self.semantic_index.clear()
                self.temporal_index.clear()
                for c_hash, entry in self.memory_bank.items():
                    if entry.get('keyword_hashes'):
                        for khash in entry['keyword_hashes']:
                            if khash not in self.semantic_index: self.semantic_index[khash] = []
                            self.semantic_index[khash].append(c_hash)
                    time_bin = self._get_timestamp_bin(entry['creation_ts'])
                    if time_bin not in self.temporal_index: self.temporal_index[time_bin] = []
                    self.temporal_index[time_bin].append(c_hash)

                self.logger.info(f"Memory loaded from {self.storage_path}, {len(self.memory_bank)} entries.")
            except FileNotFoundError:
                self.logger.warn(f"Memory file {self.storage_path} not found. Starting fresh.")
                self.memory_bank = {}
            except Exception as e:
                self.logger.error(f"Failed to load memory: {e}", exc_info=True)
                self.memory_bank = {} # Start fresh on error

    def perform_maintenance(self):
        """
        Performs memory maintenance like pruning old/irrelevant entries, re-indexing, etc.
        """
        with self.lock:
            self.logger.info("Starting memory maintenance...")
            current_time = datetime.datetime.utcnow()
            pruned_count = 0
            # Example: Prune entries below MEMORY_RETENTION_THRESHOLD that haven't been accessed recently
            # This is a very basic pruning strategy.
            # More advanced: consider access patterns, graph connectivity, etc.

            hashes_to_prune = []
            for content_hash, entry in self.memory_bank.items():
                age_seconds = (current_time - entry['last_accessed_ts']).total_seconds()
                #decay = self._calculate_relevance_decay(entry['creation_ts'], current_time) # Decay from creation
                #relevance = (entry.get('emotional_impact_score',0) + math.log1p(entry['access_count'])) * decay

                # Simpler: if old and not super impactful, and low access count
                # Use MEMORY_RETENTION_THRESHOLD from config
                is_old = age_seconds > (86400 * 30) # Example: older than 30 days since last access
                low_impact = entry.get('emotional_impact_score', 0) < (self.config.MIN_EMOTIONAL_RELEVANCE * 2) # e.g. < 0.5
                low_access = entry['access_count'] < 5

                # A more direct check against a calculated current relevance and the threshold
                decay_from_last_access = self._calculate_relevance_decay(entry['last_accessed_ts'], current_time)
                effective_relevance = (entry.get('emotional_impact_score',0) + math.log1p(entry['access_count'])) * decay_from_last_access

                if effective_relevance < self.config.MEMORY_RETENTION_THRESHOLD and is_old :
                    self.logger.debug(f"Pruning memory {content_hash} (summary: {entry['text_summary'][:30]}...) due to low relevance and age.")
                    hashes_to_prune.append(content_hash)

            for content_hash in hashes_to_prune:
                del self.memory_bank[content_hash]
                # Also remove from indexes (this can be slow, better to rebuild or manage carefully)
                # For simplicity, index rebuilding after pruning is safer if many items are removed.
                pruned_count += 1

            if pruned_count > 0:
                self.logger.info(f"Pruned {pruned_count} entries from memory.")
                # Rebuild indexes if significant changes occurred
                self._rebuild_indexes() # Assuming this method exists or is part of _load_memory logic
                self._save_memory()

            self.logger.info("Memory maintenance finished.")

    def _rebuild_indexes(self):
        self.semantic_index.clear()
        self.temporal_index.clear()
        for c_hash, entry in self.memory_bank.items():
            if entry.get('keyword_hashes'):
                for khash in entry['keyword_hashes']:
                    if khash not in self.semantic_index: self.semantic_index[khash] = []
                    self.semantic_index[khash].append(c_hash)
            time_bin = self._get_timestamp_bin(entry['creation_ts'])
            if time_bin not in self.temporal_index: self.temporal_index[time_bin] = []
            self.temporal_index[time_bin].append(c_hash)
        self.logger.info("Memory indexes rebuilt.")


# Example usage
if __name__ == '__main__':
    # Configure logger for example
    logger_instance = VictorLoggerStub(component="HyperFractalMemoryExample")
    logger_instance.log_level_str = "DEBUG"
    logger_instance.current_log_level_int = logger_instance.log_levels_map.get(logger_instance.log_level_str, 1)

    # Use default config for example
    config = ASIConfigCore()
    config.MIN_EMOTIONAL_RELEVANCE = 0.1 # Lower for testing
    config.MEMORY_RETENTION_THRESHOLD = 0.05 # Lower for testing

    memory = HyperFractalMemory(storage_path="bando_agi_persistent/test_memory.json", config=config)
    memory.logger = logger_instance # Assign more verbose logger for example

    # Clean up previous test file if any
    import os
    if os.path.exists("bando_agi_persistent/test_memory.json"):
        os.remove("bando_agi_persistent/test_memory.json")
    memory = HyperFractalMemory(storage_path="bando_agi_persistent/test_memory.json", config=config) # re-init
    memory.logger = logger_instance


    # Store some entries
    vec1 = np.random.rand(config.DIMENSIONS).astype(np.float32)
    vec2 = np.random.rand(config.DIMENSIONS).astype(np.float32)

    hash1 = memory.store_memory_entry(
        content_data={"type": "event", "details": "Met with Dr. Aris Thorne about project Chimera."},
        text_summary="Meeting with Dr. Thorne about Chimera",
        vector_embedding=vec1,
        keyword_hashes=["meeting", "thorne", "chimera_project"],
        emotional_tags={"curiosity": 0.7, "anticipation": 0.5}
    )

    time.sleep(0.1) # ensure timestamps are different

    hash2 = memory.store_memory_entry(
        content_data={"type": "concept", "definition": "A state of matter with zero viscosity."},
        text_summary="Definition of superfluidity",
        vector_embedding=vec2,
        keyword_hashes=["physics", "superfluidity", "quantum_mechanics"],
        emotional_tags={"interest": 0.6, "complexity": 0.3}
    )

    # Retrieve an entry
    retrieved_entry = memory.retrieve_memory_by_hash(hash1)
    if retrieved_entry:
        memory.logger.info(f"Retrieved by hash: {retrieved_entry['text_summary']}")

    # Search entries
    search_results_kw = memory.search_memories(keyword_hashes=["chimera_project"], top_n=1)
    memory.logger.info(f"Search by keyword 'chimera_project': {[(e['text_summary'], e.get('current_relevance_for_search')) for e in search_results_kw]}")

    query_vec_similar_to_1 = vec1 + np.random.normal(0, 0.1, vec1.shape).astype(np.float32)
    search_results_vec = memory.search_memories(query_vector=query_vec_similar_to_1, keyword_hashes=["meeting"], top_n=1) # Using keyword to narrow down
    memory.logger.info(f"Search by vector (similar to Thorne meeting): {[(e['text_summary'], e.get('similarity_score'), e.get('current_relevance_for_search')) for e in search_results_vec]}")

    # Test pruning (manual call, this would be scheduled)
    # Make one entry older and less accessed to test pruning
    if hash2 in memory.memory_bank:
         memory.memory_bank[hash2]['last_accessed_ts'] = datetime.datetime.utcnow() - datetime.timedelta(days=60)
         memory.memory_bank[hash2]['access_count'] = 1
         memory.memory_bank[hash2]['emotional_impact_score'] = 0.11 # Just above MIN_EMOTIONAL_RELEVANCE
         memory._save_memory() # save this change before maintenance

    memory.logger.info("Performing maintenance...")
    memory.perform_maintenance()

    if not memory.retrieve_memory_by_hash(hash2): # Should be pruned if conditions met
        memory.logger.info("Entry for 'superfluidity' was pruned as expected (or conditions not met).")
    else:
        memory.logger.info("Entry for 'superfluidity' was NOT pruned.")

    memory.logger.info(f"Final memory size: {len(memory.memory_bank)}")
    # Clean up test file
    # if os.path.exists("bando_agi_persistent/test_memory.json"):
    #     os.remove("bando_agi_persistent/test_memory.json")
