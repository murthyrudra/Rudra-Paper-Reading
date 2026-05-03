# Systematic Knowledge Injection into Large Language Models via Diverse Augmentation for Domain-Specific RAG

**Authors:** Kushagra Bhushan, Yatin Nandwani, Dinesh Khandelwal, Sonam Gupta  
**Venue:** NAACL 2025  
**Year:** 2026  
**Paper:** [https://aclanthology.org/2025.findings-naacl.329.pdf](https://aclanthology.org/2025.findings-naacl.329.pdf)  
**Category:** RAG  
**Tags:** `RAG`

---

## 📄 Abstract
Retrieval-Augmented Generation (RAG) has emerged as a prominent method for incorporating domain knowledge into Large Language Models (LLMs). While RAG enhances response relevance by incorporating retrieved domain knowledge in the context, retrieval errors can still lead to hallucinations and incorrect answers. To recover from retriever failures, domain knowledge is injected by fine-tuning the model to generate the correct response, even in the case of retrieval errors. However, we observe that without systematic knowledge augmentation, fine-tuned LLMs may memorize new information but still fail to extract relevant domain knowledge, leading to poor performance. In this work, we present a novel framework that significantly enhances the fine-tuning process by augmenting the training data in two ways -- context augmentation and knowledge paraphrasing. In context augmentation, we create multiple training samples for a given QA pair by varying the relevance of the retrieved information, teaching the model when to ignore and when to rely on retrieved content. In knowledge paraphrasing, we fine-tune with multiple answers to the same question, enabling LLMs to better internalize specialized knowledge. To mitigate catastrophic forgetting due to fine-tuning, we add a domain-specific identifier to a question and also utilize a replay buffer containing general QA pairs. Experimental results demonstrate the efficacy of our method over existing techniques, achieving up to 10\% relative gain in token-level recall while preserving the LLM's generalization capabilities.
---

## 🎯 Key Contributions

1. RAG suffers from retrieval errors and hallucinations, and fine-tuning alone may not resolve this issue.
2. Domain knowledge needs to be ingested into the LLM's weights via finetuning.
3. Finetuning may lead to memorization and the LLM may fail to extract relevant information from the context during inference.
4. Enhance finetuning via
    - Context Augmentation: Create multiple training samples for a given QA pair by varying the relevance of the retrieved information.
    - Knowledge Paraphrasing: Finetune with multiple answers (paraphrased versions) for the same question.
    - To mitigate catastrophic forgetting, add a domain-specific indetifier to the question and utilize a replay buffer.

---

## 🔍 Motivation

1. When retriever succeeds, an LLM should be able to leverage the retrieved information to answer the question.
2. When retriever fails, an LLM should be able to answer the question using its own knowledge.
3. Conditional Memorization Bias: Each question should not be assigned to retrieval failure or suceeds scenario exclusively. Assume, all questions in training data are from retrieval success scenario. --> the LLM will rely on using contextual information and no updation of internal peramaters happens. Similarly, if all questions are from retrieval failure scenario, the LLM will rely on its own knowledge and during inference it won't use contextual information.
4. Canonical Question Overfitting: LLM's ability to generate diverse and nuanced responses depending on retrieved context is hindered if every question has only one answer. 


## Approach

### Synthetic Question-Answer Generation

1. Given a set of documents, synthetic QA pairs are generated using a LLM.
2. Generate multiple QA pairs for each document to ensure coverage.
3. Reprompt the LLM to generate multiple answers for the same question to encourage diversity.

### Context Augmented-RAFT Finetuning (CA-RAFT)

1. Given a set of documents and QA pairs, the instance is classified as retrieval success or failure.
2. CA-RAFT contains one set where are QA pairs are paired with distractor documents only.
3. CA-RAFT contains another set where are QA pairs are paired with gold documents and distractor documents.

### Paraphrase Augmented-RAFT Finetuning (PA-RAFT)

1. Enhances CA-RAFT by augmenting paraphrases of answers.
2. Add domain identifier to the prompt to inform the LLM that each question is tied to the domain.

### Self-Selective Replay Buffer:

1. Mitigate catastrophic forgetting by adding replay buffer along with domain-specific finetuning.
2. Generate large-scale prompts using taxonomy to ensure coverage across domains.
3. Pass the prompts through the LLM to generate responses which acts as replay buffer.


---

## 📊 Results

1. Construct test set consisting of factoid questions.
2. Drop instances where the answers contains reference to the passage as in "In the provided context" etc using a LLM.
3. Use token-level recall and LLM Judges to test the accuracy of the generated answers.

### Baselines

1. Domain-Specific Finetuning (DSF): The LLM is finetuned on the synthetic QA pairs. 
2. DSF + RAG: The DSF model is prompted with retrieved documents during inference only.
3. RAFT: Perform finetuning with retrieved documents and QA triplets. The instances can fall into either retrieval success or failure scenarios only.
4. CA-RAFT: Perform finetuning with retrieved documents and QA triplets. The instances fall into both retrieval success and failure scenarios.

### Main Results

1. PA-RAG outperforms all baselines in terms of token-level recall and LLM Judge scores on retrieval failure instances.
2. CA-RAFT performs better than RAFT indicating the evidence of conditional memorization bias.

### Ablations

1. Dropping Domain Identifier results in negligible drop in performance.
    - The drop is large on *no overlap* subset indicating that the identifier helps the LLM in recalling the new domain information from its internal state.
2. Dropping replay buffer leads to the largest drop in performance. 
    - It negatively affects the *some overlap* subset indicating the comprehension capability of the model being affected.
3. Using single answer for every question also leads to significant drop in performance.

### Proof of Conditional Memorization Bias

1. Assume we have 5 chapters 1, 2, 3, 4, and 5. QA pairs from chapters 1, 2, and 3 are assigned to retrival failure bucket and 4, 5 are added to retrieval success bucket.
2. During retrieval failure, 
    - performance on chapter 4 and 5 is significantly poor compared to chapter 1, 2, and 3.
    - The model relied on context provided for chapter 4 and 5 and failed to memorize the knowledge.
    - performance on chapter 1, 2, and 3 is lower compared to chapter 4 and 5 when retriever succeeds.
    - The model relied on its internal state only and failed to use the contextual information provided.


---

## 🏷️ Tags for Reference

#rag

---

**Date Read:** 2026-05-02  
**Status:** ✅ Completed
