"""Text chunking service for knowledge base."""
import re
from typing import List


class TextChunker:
    """
    Service for chunking text into smaller pieces.
    
    Uses semantic boundaries (sentences, paragraphs) when possible.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Target chunk size in tokens (approximate)
            chunk_overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
        
        Returns:
            List of text chunks
        """
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Group sentences into chunks
        chunks = self._group_sentences(sentences)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for chunking.
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
        
        Returns:
            List of sentences
        """
        # Simple sentence splitting (handles most cases)
        # More sophisticated: use spaCy or NLTK
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _group_sentences(self, sentences: List[str]) -> List[str]:
        """
        Group sentences into chunks.
        
        Args:
            sentences: List of sentences
        
        Returns:
            List of chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # Approximate token count (words * 1.3)
            sentence_tokens = len(sentence.split()) * 1.3
            
            # Check if adding this sentence would exceed chunk size
            if current_length + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.chunk_overlap,
                )
                current_chunk = overlap_sentences
                current_length = sum(len(s.split()) * 1.3 for s in overlap_sentences)
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _get_overlap_sentences(
        self,
        sentences: List[str],
        overlap_tokens: int,
    ) -> List[str]:
        """
        Get last few sentences for overlap.
        
        Args:
            sentences: List of sentences
            overlap_tokens: Target overlap in tokens
        
        Returns:
            List of overlap sentences
        """
        overlap = []
        total_tokens = 0
        
        # Take sentences from end until we reach overlap size
        for sentence in reversed(sentences):
            sentence_tokens = len(sentence.split()) * 1.3
            
            if total_tokens + sentence_tokens > overlap_tokens:
                break
            
            overlap.insert(0, sentence)
            total_tokens += sentence_tokens
        
        return overlap
    
    def chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Chunk text by paragraphs (alternative strategy).
        
        Args:
            text: Text to chunk
        
        Returns:
            List of paragraph chunks
        """
        # Split by double newline
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = len(para.split()) * 1.3
            
            # If single paragraph exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Chunk the large paragraph
                para_chunks = self.chunk_text(para)
                chunks.extend(para_chunks)
                continue
            
            # Check if adding this paragraph would exceed chunk size
            if current_length + para_tokens > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(para)
            current_length += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
