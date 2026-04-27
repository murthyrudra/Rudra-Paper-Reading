# Synthetic continued pretraining

**Authors:** Zitong Yang, Neil Band, Shuangping Li, Emmanuel Candes  
**Venue:** ICLR 2025  
**Year:** 2026  
**Paper:** [https://iclr.cc/virtual/2025/poster/31270](https://iclr.cc/virtual/2025/poster/31270)  
**Category:** Other  
**Tags:** `RAG`

---

## 📄 Abstract

Pretraining on large-scale, unstructured internet text enables language models to acquire a significant amount of world knowledge. However, this knowledge acquisition is data-inefficient—to learn a fact, models must be trained on hundreds to thousands of diverse representations of it. This poses a challenge when adapting a pretrained model to a small corpus of domain-specific documents, where each fact may appear rarely or only once. We propose to bridge this gap with synthetic continued pretraining: using the small domain-specific corpus to synthesize a large corpus more amenable to learning, and then performing continued pretraining on the synthesized corpus. We instantiate this proposal with EntiGraph, a synthetic data augmentation algorithm that extracts salient entities from the source corpus and then generates diverse text by drawing connections between those entities. Synthetic continued pretraining with EntiGraph enables a language model to answer questions and follow generic instructions related to the source documents without access to them. If the source documents are instead available at inference time, we show that the knowledge acquired through our approach compounds with retrieval-augmented generation. To better understand these results, we build a simple mathematical model of EntiGraph, and show how synthetic data augmentation can “rearrange” knowledge to enable more data-efficient learning.

---

## 🎯 Key Contributions
1. How to ingest new knowledge from small corpora into a LLM?
2. Simple paraphrase or rewrite is insufficient as it does not cover the gap in the diversity of knowledge representations.
3. EntiGraph - an entity-centric augmentation algorithm.
    - Breaks a corpus into a list of entities and then uses a LLM to describe the relations between the entities
4. Generates 455M synthetic tokens from 1.3M real tokens using GPT-4.
5. Continually pre-train a Llama model and evaluate on MCQs without access to source data.
6. Log-linear scaling in accuracy is observed. 

---

## 🔍 Methodology
1. **Entity Extraction:**
    - Extract a list of entities from the corpus using a LLM.
2. **Realtion Anslysis:**
    - Given a set of entities, analyse and describe how the entities interact within the context of the document.


**Date Read:** 2026-04-27  
**Status:** ✅ Completed
