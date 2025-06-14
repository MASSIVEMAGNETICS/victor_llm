import json
import hashlib
import datetime
import threading
import numpy as np
import math
import time # Added for decay calculation example
import os # Added for FAISS
import faiss # Added for FAISS

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

        # FAISS related initialization
        self.faiss_index_path = self.storage_path.replace('.json', '_faiss.index')
        self.faiss_index = None
        self.int_id_to_content_hash = {} # Maps FAISS integer IDs back to content_hash strings

        self._load_memory() # Loads memory_bank, then calls _load_faiss_index
        self.logger.info(f"HyperFractalMemory initialized. Loaded {len(self.memory_bank)} entries. FAISS index {'loaded' if self.faiss_index and self.faiss_index.ntotal > 0 else 'initialized'}.")

    def _content_hash_to_int_id(self, content_hash: str) -> int:
        """Converts a hex content_hash to a non-negative integer for FAISS."""
        # Using int(hash, 16) should be fine for IndexIDMap2 which supports uint64 IDs.
        # Python integers handle arbitrary size, FAISS IDs are typically int64.
        # Ensure it's non-negative, though SHA256 hex is usually positive when converted.
        return int(content_hash, 16)

    def _load_faiss_index(self):
        """Loads FAISS index from disk or creates a new one if not found or loading fails."""
        if os.path.exists(self.faiss_index_path):
            try:
                self.faiss_index = faiss.read_index(self.faiss_index_path)
                # Also need to load the int_id_to_content_hash map, assume it's implicitly handled
                # by rebuilding from memory_bank if not saved separately, or save/load it too.
                # For now, we will rebuild int_id_to_content_hash from memory_bank after loading faiss_index
                # to ensure consistency, especially if the map wasn't saved with the index.
                self.int_id_to_content_hash.clear()
                # This relies on memory_bank being loaded first.
                for content_hash, entry in self.memory_bank.items():
                    if entry.get('vector_embedding') is not None:
                        faiss_id = self._content_hash_to_int_id(content_hash)
                        # Check if ID is actually in index; if not, it's an inconsistency or stale index.
                        # For robust loading, one might verify IDs or rebuild if inconsistencies are found.
                        # For now, assume loaded index is consistent with hashes in memory_bank.
                        self.int_id_to_content_hash[faiss_id] = content_hash
                self.logger.info(f"FAISS index loaded from {self.faiss_index_path}. Index size: {self.faiss_index.ntotal} vectors. Map size: {len(self.int_id_to_content_hash)}")
            except Exception as e:
                self.logger.error(f"Failed to load FAISS index from {self.faiss_index_path}: {e}. Creating a new one.", exc_info=True)
                self.faiss_index = None # Ensure it's None so a new one is created

        if self.faiss_index is None:
            self.logger.info("Creating a new FAISS index.")
            # Ensure DIMENSIONS is a valid integer
            if not hasattr(self.config, 'DIMENSIONS') or not isinstance(self.config.DIMENSIONS, int) or self.config.DIMENSIONS <= 0:
                self.logger.error(f"Invalid or missing DIMENSIONS in config: {getattr(self.config, 'DIMENSIONS', 'Not set')}. Cannot initialize FAISS index.")
                return # Cannot proceed without dimensions

            self.faiss_index = faiss.IndexIDMap2(faiss.IndexFlatL2(self.config.DIMENSIONS))
            self.int_id_to_content_hash.clear() # Clear any previous mappings

            # Populate the new index and map with existing entries from memory_bank
            # This assumes _load_memory (which calls this) has already populated self.memory_bank
            populated_count = 0
            for content_hash, entry in self.memory_bank.items():
                if entry.get('vector_embedding') is not None:
                    try:
                        vec = np.array([entry['vector_embedding']], dtype=np.float32)
                        if vec.shape[1] != self.config.DIMENSIONS:
                            self.logger.warn(f"Vector for {content_hash} has dimension {vec.shape[1]}, expected {self.config.DIMENSIONS}. Skipping.")
                            continue
                        faiss_id = self._content_hash_to_int_id(content_hash)
                        self.faiss_index.add_with_ids(vec, np.array([faiss_id]))
                        self.int_id_to_content_hash[faiss_id] = content_hash
                        populated_count += 1
                    except Exception as e:
                        self.logger.error(f"Error adding vector for {content_hash} to new FAISS index: {e}", exc_info=True)
            self.logger.info(f"New FAISS index created and populated with {populated_count} vectors from memory_bank.")
            if populated_count > 0:
                self._save_faiss_index() # Save immediately if populated

    def _save_faiss_index(self):
        """Saves the FAISS index to disk."""
        if self.faiss_index is not None:
            try:
                faiss.write_index(self.faiss_index, self.faiss_index_path)
                self.logger.debug(f"FAISS index saved to {self.faiss_index_path}. Index size: {self.faiss_index.ntotal}")
                # Consider saving int_id_to_content_hash map here as well if it becomes large or complex to rebuild
            except Exception as e:
                self.logger.error(f"Failed to save FAISS index: {e}", exc_info=True)

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

            # Add to FAISS index
            if vector_embedding is not None and self.faiss_index is not None:
                try:
                    vec = np.array([entry['vector_embedding']], dtype=np.float32)
                    if vec.shape[1] == self.config.DIMENSIONS: # Check dimension consistency
                        faiss_id = self._content_hash_to_int_id(content_hash)
                        self.faiss_index.add_with_ids(vec, np.array([faiss_id]))
                        self.int_id_to_content_hash[faiss_id] = content_hash
                        # self._save_faiss_index() # Consider batching saves or saving with main memory
                    else:
                        self.logger.warn(f"Vector for {content_hash} not added to FAISS due to dimension mismatch ({vec.shape[1]} vs {self.config.DIMENSIONS}).")
                except Exception as e:
                    self.logger.error(f"Error adding vector for {content_hash} to FAISS index: {e}", exc_info=True)


            self.logger.info(f"Stored new memory entry {content_hash} for: {text_summary[:50]}")
            self._save_memory() # Persist after important change (this will also save FAISS index)
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
            faiss_retrieved_hashes = set()

            if query_vector is not None and self.faiss_index is not None and self.faiss_index.ntotal > 0:
                try:
                    q_vec = np.array([query_vector], dtype=np.float32)
                    if q_vec.shape[1] != self.config.DIMENSIONS:
                        self.logger.warn(f"Query vector dimension mismatch ({q_vec.shape[1]} vs {self.config.DIMENSIONS}). FAISS search skipped.")
                    else:
                        # Increase k for FAISS search slightly to allow for filtering non-existent hashes
                        k_faiss = top_n + 5
                        distances, faiss_ids_arr = self.faiss_index.search(q_vec, k_faiss)
                        faiss_ids_list = faiss_ids_arr[0].tolist()

                        for fid in faiss_ids_list:
                            if fid != -1: # -1 indicates no more neighbors
                                content_hash = self.int_id_to_content_hash.get(fid)
                                if content_hash:
                                    faiss_retrieved_hashes.add(content_hash)
                                else:
                                    self.logger.warn(f"FAISS returned ID {fid} not found in int_id_to_content_hash map.")
                        self.logger.debug(f"FAISS search returned {len(faiss_retrieved_hashes)} candidate hashes.")
                        candidate_hashes.update(faiss_retrieved_hashes)
                except Exception as e:
                    self.logger.error(f"Error during FAISS search: {e}", exc_info=True)

            if keyword_hashes:
                keyword_candidate_hashes = set()
                for khash in keyword_hashes:
                    keyword_candidate_hashes.update(self.semantic_index.get(khash, []))

                if query_vector is not None and len(faiss_retrieved_hashes) > 0 :
                    # If vector search also happened, take intersection or union based on strategy
                    # For now, let's take union, allowing keywords to add more candidates
                    candidate_hashes.update(keyword_candidate_hashes)
                    self.logger.debug(f"Combined FAISS and keyword search. Total candidates: {len(candidate_hashes)}")
                elif len(keyword_candidate_hashes) > 0:
                    candidate_hashes.update(keyword_candidate_hashes)
                    self.logger.debug(f"Keyword search returned {len(keyword_candidate_hashes)} candidate hashes.")


            # If no candidates from FAISS or keywords, and vector query, we might still need to scan all
            # if the user expects it. For now, if candidate_hashes is empty, result is empty.
            if not candidate_hashes and query_vector is not None and not keyword_hashes:
                 # This is where a full scan might happen if FAISS is empty or not used.
                 # However, with FAISS, if it's populated, it should yield results.
                 # If FAISS is empty, this means no vectors are indexed.
                 self.logger.debug("No candidates from FAISS or keywords for vector query. Consider if all memories should be scanned.")


            retrieved_entries = []
            current_time = datetime.datetime.utcnow()

            for c_hash in list(candidate_hashes):
                entry = self.memory_bank.get(c_hash)
                if not entry: continue

                # Temporal filter
                if date_range:
                    entry_ts = entry['creation_ts']
                    if not (date_range[0] <= entry_ts <= date_range[1]):
                        continue

                decay = self._calculate_relevance_decay(entry['creation_ts'], current_time)
                current_relevance = (entry.get('emotional_impact_score',0.1) + math.log1p(entry.get('access_count',1))) * decay
                entry['current_relevance_for_search'] = current_relevance

                if current_relevance < self.config.MEMORY_RETENTION_THRESHOLD :
                    continue

                if query_vector is not None and entry.get('vector_embedding') is not None:
                    entry_vec = np.array(entry['vector_embedding'])
                    # Ensure dimensions match before similarity calculation
                    if entry_vec.ndim == 1 and query_vector.ndim == 1 and entry_vec.shape[0] == query_vector.shape[0]:
                        similarity = np.dot(query_vector, entry_vec) / (np.linalg.norm(query_vector) * np.linalg.norm(entry_vec))
                        entry['similarity_score'] = similarity
                        if similarity < min_relevance:
                            continue
                    else:
                        self.logger.warn(f"Skipping similarity calculation for {c_hash} due to mismatched vector dimensions or type.")
                        if query_vector is not None : continue # If query vector exists, similarity is a must
                elif query_vector is not None: # Query has vector, but entry doesn't
                    continue

                retrieved_entries.append(entry)

            def sort_key(e):
                sim = e.get('similarity_score', -1 if query_vector is not None else 0) # if no query vec, sim is irrelevant
                rel = e.get('current_relevance_for_search', 0)
                return (sim, rel)

            retrieved_entries.sort(key=sort_key, reverse=True)
            self.logger.info(f"Search processed {len(candidate_hashes)} candidates, found {len(retrieved_entries)} matching entries, returning top {top_n}.")
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

            # Save FAISS index whenever main memory is saved
            self._save_faiss_index()

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
                # self.int_id_to_content_hash.clear() # This is cleared and rebuilt in _load_faiss_index or _rebuild_indexes

                for c_hash, entry in self.memory_bank.items():
                    if entry.get('keyword_hashes'):
                        for khash in entry['keyword_hashes']:
                            if khash not in self.semantic_index: self.semantic_index[khash] = []
                            self.semantic_index[khash].append(c_hash)
                    time_bin = self._get_timestamp_bin(entry['creation_ts'])
                    if time_bin not in self.temporal_index: self.temporal_index[time_bin] = []
                    self.temporal_index[time_bin].append(c_hash)
                    # FAISS index population is handled by _load_faiss_index called after this block.

                self.logger.info(f"Memory bank loaded from {self.storage_path}, {len(self.memory_bank)} entries.")
            except FileNotFoundError:
                self.logger.warn(f"Memory file {self.storage_path} not found. Starting fresh.")
                self.memory_bank = {} # Ensure memory_bank is empty before FAISS init
            except Exception as e:
                self.logger.error(f"Failed to load memory: {e}", exc_info=True)
                self.memory_bank = {} # Start fresh on error

            # Load or initialize FAISS index after memory_bank is populated (or empty)
            self._load_faiss_index()


    def perform_maintenance(self):
        """
        Performs memory maintenance like pruning old/irrelevant entries, re-indexing, etc.
        """
        with self._lock: # Changed from self.lock to self._lock
            self.logger.info("Starting memory maintenance...")
            current_time = datetime.datetime.utcnow()
            pruned_count = 0

            hashes_to_prune = []
            faiss_ids_to_remove = []

            for content_hash, entry in self.memory_bank.items():
                age_seconds = (current_time - entry['last_accessed_ts']).total_seconds()
                is_old = age_seconds > (86400 * 30)

                decay_from_last_access = self._calculate_relevance_decay(entry['last_accessed_ts'], current_time)
                effective_relevance = (entry.get('emotional_impact_score',0) + math.log1p(entry['access_count'])) * decay_from_last_access

                if effective_relevance < self.config.MEMORY_RETENTION_THRESHOLD and is_old :
                    self.logger.debug(f"Pruning memory {content_hash} (summary: {entry['text_summary'][:30]}...) due to low relevance and age.")
                    hashes_to_prune.append(content_hash)
                    if entry.get('vector_embedding') is not None:
                        faiss_id = self._content_hash_to_int_id(content_hash)
                        faiss_ids_to_remove.append(faiss_id)


            if self.faiss_index is not None and faiss_ids_to_remove:
                try:
                    remove_result = self.faiss_index.remove_ids(np.array(faiss_ids_to_remove, dtype=np.int64))
                    self.logger.info(f"Attempted to remove {len(faiss_ids_to_remove)} IDs from FAISS index. Removed: {remove_result}")
                    # Update map
                    for fid_to_remove in faiss_ids_to_remove:
                        if fid_to_remove in self.int_id_to_content_hash:
                            del self.int_id_to_content_hash[fid_to_remove]
                except Exception as e:
                    self.logger.error(f"Error removing IDs from FAISS index: {e}", exc_info=True)


            for content_hash in hashes_to_prune:
                if content_hash in self.memory_bank: # Check existence before del
                    del self.memory_bank[content_hash]
                    pruned_count += 1
                # Semantic and temporal indexes will be rebuilt by _rebuild_indexes if called

            if pruned_count > 0:
                self.logger.info(f"Pruned {pruned_count} entries from memory bank.")
                # Rebuild other indexes if significant changes occurred
                self._rebuild_indexes() # This will also rebuild FAISS index
                self._save_memory() # Save changes including the (rebuilt) FAISS index

            self.logger.info("Memory maintenance finished.")

    def _rebuild_indexes(self):
        self.semantic_index.clear()
        self.temporal_index.clear()

        # Rebuild FAISS index and its ID map
        if hasattr(self.config, 'DIMENSIONS') and isinstance(self.config.DIMENSIONS, int) and self.config.DIMENSIONS > 0:
            self.logger.info("Rebuilding FAISS index...")
            self.faiss_index = faiss.IndexIDMap2(faiss.IndexFlatL2(self.config.DIMENSIONS))
            self.int_id_to_content_hash.clear()
            populated_faiss_count = 0
            for c_hash, entry in self.memory_bank.items(): # Iterate through current memory_bank
                # Rebuild semantic and temporal
                if entry.get('keyword_hashes'):
                    for khash in entry['keyword_hashes']:
                        if khash not in self.semantic_index: self.semantic_index[khash] = []
                        self.semantic_index[khash].append(c_hash)
                time_bin = self._get_timestamp_bin(entry['creation_ts'])
                if time_bin not in self.temporal_index: self.temporal_index[time_bin] = []
                self.temporal_index[time_bin].append(c_hash)

                # Populate FAISS
                if entry.get('vector_embedding') is not None and self.faiss_index is not None:
                    try:
                        vec = np.array([entry['vector_embedding']], dtype=np.float32)
                        if vec.shape[1] == self.config.DIMENSIONS:
                            faiss_id = self._content_hash_to_int_id(c_hash)
                            self.faiss_index.add_with_ids(vec, np.array([faiss_id]))
                            self.int_id_to_content_hash[faiss_id] = c_hash
                            populated_faiss_count +=1
                        else:
                             self.logger.warn(f"During rebuild, vector for {c_hash} has dimension {vec.shape[1]}, expected {self.config.DIMENSIONS}. Skipping.")
                    except Exception as e:
                        self.logger.error(f"Error adding vector for {c_hash} to FAISS index during rebuild: {e}", exc_info=True)
            self.logger.info(f"FAISS index rebuilt and populated with {populated_faiss_count} vectors.")
        else:
            self.logger.warn("FAISS index not rebuilt because DIMENSIONS is not configured correctly.")
            # Still rebuild other indexes
            for c_hash, entry in self.memory_bank.items():
                if entry.get('keyword_hashes'):
                    for khash in entry['keyword_hashes']:
                        if khash not in self.semantic_index: self.semantic_index[khash] = []
                        self.semantic_index[khash].append(c_hash)
                time_bin = self._get_timestamp_bin(entry['creation_ts'])
                if time_bin not in self.temporal_index: self.temporal_index[time_bin] = []
                self.temporal_index[time_bin].append(c_hash)

        self.logger.info("Memory indexes (semantic, temporal) rebuilt.")


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
