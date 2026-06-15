# Ragged Taxonomy Builder (Local LLM with Ollama)

A compact workflow for generating a ragged, human‑friendly taxonomy using local LLM inference. No API keys or cloud services required. The resulting taxonomy is then reshaped into a structure suitable for import into ACDSee category hierarchies.

## What Ollama Is

Ollama is a local LLM runner that downloads models to your machine and serves them through a lightweight HTTP API. It works like a self‑hosted chat endpoint: once a model is pulled, you can query it repeatedly with no cost, no rate limits, and no internet connection. All inference happens locally, so taxonomy data never leaves your machine.

This project uses Ollama to infer short, common English group names for each biological family. These inferred groups are then used to build a clean, three‑level hierarchy that can be transformed into ACDSee’s category XML format.

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

After building this ragged taxonomy, the data can be reshaped into the hierarchical XML structure required by ACDSee, allowing the entire taxonomy to appear as nested categories under a top‑level “Wildlife” node.

## Installing Ollama

1. Download from https://ollama.ai  
2. Install normally  
3. Start the service:  
