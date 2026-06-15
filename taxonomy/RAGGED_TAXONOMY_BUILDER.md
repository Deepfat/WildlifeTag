# Ragged Taxonomy Builder (Local LLM with Ollama)

A compact workflow for generating a ragged, human‑friendly taxonomy using local LLM inference. No API keys or cloud services required.

## What Ollama Is

Ollama is a local LLM runner that downloads models to your machine and serves them through a lightweight HTTP API. It works like a self‑hosted chat endpoint: once a model is pulled, you can query it repeatedly with no cost, no rate limits, and no internet connection. All inference happens locally, so taxonomy data never leaves your machine.

Ollama exposes an API on `http://localhost:11434` and supports both interactive chat and programmatic requests. This project uses that API to ask the model for short, common English group names for each biological family.

## Overview

The builder converts scientific taxonomy data from `taxonomy.json` into a three‑level hierarchy:

- **Class** — birds, mammals, reptiles, insects  
- **Group** — inferred common grouping (owls, raptors, songbirds, cats)  
- **Family** — biological family (strigidae, passeridae, felidae)  
- **Leaf** — species common name (Barn Owl, House Sparrow, Lion)

Example:

class | group | family | common_name  
------|--------|--------|-------------  
birds | owls | strigidae | Barn Owl  
birds | owls | strigidae | Snowy Owl  
birds | songbirds | passeridae | House Sparrow  
mammals | cats | felidae | Lion  
mammals | primates | hominidae | Human  

## Installing Ollama

1. Download from https://ollama.ai  
2. Install normally  
3. Start the service:  
