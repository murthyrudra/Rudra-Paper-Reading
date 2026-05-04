# From Local to Global: A Graph RAG Approach to Query-Focused Summarization

**Authors:** Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley  
**Venue:** Manual  
**Year:** 2026  
**Paper:** [arXiv](arXiv)  
**Category:** RAG  
**Tags:** `RAG`

---

## 📄 Abstract
The use of retrieval-augmented generation (RAG) to retrieve relevant information from an external knowledge source enables large language models (LLMs) to answer questions over private and/or previously unseen document collections. However, RAG fails on global questions directed at an entire text corpus, such as "What are the main themes in the dataset?", since this is inherently a query-focused summarization (QFS) task, rather than an explicit retrieval task. Prior QFS methods, meanwhile, do not scale to the quantities of text indexed by typical RAG systems. To combine the strengths of these contrasting methods, we propose GraphRAG, a graph-based approach to question answering over private text corpora that scales with both the generality of user questions and the quantity of source text. Our approach uses an LLM to build a graph index in two stages: first, to derive an entity knowledge graph from the source documents, then to pregenerate community summaries for all groups of closely related entities. Given a question, each community summary is used to generate a partial response, before all partial responses are again summarized in a final response to the user. For a class of global sensemaking questions over datasets in the 1 million token range, we show that GraphRAG leads to substantial improvements over a conventional RAG baseline for both the comprehensiveness and diversity of generated answers.


---

## 🎯 Key Takeaway

1. Existing RAG systems are good at retrieving specific piece of information
2. It fails on global questions which are directed at an entire text corpus
3. For example, "What are the main themes of this dataset?"
4. Such queries are also called as **Query Focused Summarization**
5. GraphRAG proposes an approach which can tackle both local and global queries
6. Graph RAG uses an LLM to generate to construct a knowledge graph where nodes represents entities and edges represents relationships between entities
7. Partitions the graph into hierarchy of communities of closely related entities before using a LLM to generate summaries for the community
8. The summaries are generated in a bottoms-up manner where the lower-level nodes' summaries are generated first. This lower-level nodes' summary is incorporated while generating top-level nodes' summary
9. GrapgRAG uses map-reduce processing to answer queries. The map step involves generating partial answers to the queries based on the community summaries. The reduce step involves using all partial answers to generate the combined answer to the query

---

## Motivation

1. Vector RAG focuses on retrieving a small set of documents that are most relevant to the query and fits within the context window of the LLM
2. The LLM generates a responses based on the retrieved documents
3. Vector RAG fails on sensemaking queries
4. Consider the query **What's the outlook of the agricultural production for the year 2025 in Guntur district?**
    - This query requires collecting information about the agricultural production in Guntur district for the year 2025 across all crop varieties and summarizing them.

> [!NOTE]
> Sensemaking tasks require reasoning over connected entities in order to anticipate their tracjectories and act effectively

5. Given a query and a text with implicit interconnected concepts, an LLM can generate a summary that answers the query.
6. When the volume of data requires RAG, vector RAG fails to support sensemaking queries.


## 🔍 Methodology

### Chunking
1. The corpus is split into chunks. Longer chunks results in fewer LLM calls but suffer from recall degradation.
    - **Self-Reflection** is employed to improve recall. LLM is prompted to extract entities from the chunk. It is then prompted again asking if any entities are missed. If yes, the LLM is prompted again to extract the missed entities. This is repeated *k* times

### Knowledge Graph Construction
1. The LLM is prompted to extract important entities and the relationships between the entities from the given chunk. 
2. The LLM also generates short descriptions for the entities and the relationships.
3. The LLM can also be prompted to extract claims about detected entities.
4. In-context learning with domain-specific examples are used.
5. Entities becomes nodes and relationships become edges. Descriptions are aggregated and summarized for each node and edge.

### Graph Communities
1. Leiden community detection in a hierarchical manner, recursively detecting sub-communities within each detected community until reaching leaf communities that can no longer be partitioned.
2. Eacl level in the hierarchy provides a community partition that covers the nodes in mutually exclusive, collectively exhaustive way.

### Community Summaries
1. Create report-like summaries for each node
2. Start with leaf-node summaries and add it to the prompt. Also add add descriptions of the source node, target node, the edge itself, and related claims.
3. This is used to generate summary for a particular community (non-leaf node).

### Global Answer
1. Community summaries are randomly shuffled and divided into chunks of pre-specified size
2. Generate intermediate answers in parallel and also a rating between 0-100 on how informative each community is for answering the query
3. Drop communities with rating of 0
4. Intermediate community answers are sorted in descending order
of helpfulness score and iteratively added into a new context window until the token limit is reached. This final context is used to generate the global answer returned to the user


### Global Sensemaking Question Generation
1. LLM is used to generate a set of corpus-specific questions designed to asses high-level understanding of a given corpus
2. The answer to the queries shouldn't require any retrieval of specific low-level facts or details.
3. Given a high-level description of the corpus, the LLM is prompted to generate hypothetical users
4. The LLM is then prompted to generate a set of tasks that an hypothetical user might want to ask about the corpus
5. For each combination of user and task, the LLM is prompted to generate a question that require understanding of the corpus

### Evaluation
1. Use LLM evaluator that judges relative performance according to given criteria
2. The criteria are
    - Comprehensiveness: How much detail does the answer provide to cover all aspects and details of the question?
    - Diversity: How varied and rich is the answer in providing different perspectives and insights on the question?
    - Empowerment: How well does the answer help the reader understand and make informed judgments about the topic?
3. LLM is provided with the question, generated answer from two systems and prompted to compare the answers based on the criteria

### Datasets
1. Podcast Transcripts
2. News Articles

---

## 📊 Results

### Baseline
1. C0: Only root-level community summaries to answer user queries
2. C1: Uses high-level community summaries to answer user queries. These are sub-communities of root-level community.
3. C2: Uses intermediate-level community summaries to answer user queries. These are sub-communities of C1.
4. C3: Uses leaf-level community summaries to answer user queries. These are sub-communities of C2.
4. TS: Uses source text rather than community summaries. 
5. SS: Uses Vector RAG 

### Results
1. Global approaches outperform conventional RAG

---

## Limitations
1. Works only on queries which require global understanding of the corpus

---

## 🏷️ Tags for Reference

#rag

---

**Date Read:** 2026-05-04  
**Status:** 📖 In Progress / ✅ Completed / 🔄 Revisit
