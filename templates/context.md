# DSA Memory Trainer

## Overview

DSA Memory Trainer is an AI-assisted learning platform designed to improve long-term retention of Data Structures and Algorithms concepts, patterns, and problem-solving approaches.

Unlike traditional coding practice platforms that focus primarily on solving problems, this application focuses on helping users remember how they solved problems and why specific approaches were chosen.

The system acts as a personal knowledge repository where users can log solved problems, store their thought process, and periodically revisit those problems through structured practice sessions.

The objective is to strengthen pattern recognition and improve recall of solution strategies over time.

---

# Motivation

Many developers solve a large number of LeetCode problems but struggle to remember the underlying patterns and approaches after a few weeks.

Common issues include:

* Forgetting previously solved problems
* Memorizing solutions instead of understanding patterns
* Difficulty identifying when a known pattern applies
* Inability to recall the reasoning process behind a solution

This project aims to address these problems by creating a dedicated memory reinforcement system for DSA learning.

---

# Core Idea

The application revolves around two primary workflows:

### Question Logging

Users log problems they have solved along with their personal explanation of the solution approach.

The focus is not on storing code but on capturing:

* Key observations
* Problem-solving strategy
* Chosen pattern
* Important insights
* Mental model used to solve the problem

This creates a searchable personal database of DSA knowledge.

### Practice and Recall

The application periodically presents previously logged questions for review.

Instead of showing the original problem statement directly, the system generates a rephrased version of the problem.

Users must then recall and describe the solution approach from memory.

The AI evaluates the response and provides feedback on the quality of recall.

This process encourages active recall rather than passive review.

---

# Key Features

## Question Repository

Maintain a structured collection of solved DSA problems.

Each entry contains:

* LeetCode problem identifier
* Problem title
* User approach
* Extracted pattern
* Difficulty information
* Creation timestamp

---

## AI-Based Question Rephrasing

The original problem statement can be rewritten using different wording while preserving the same constraints and logic.

This prevents users from relying on memorized wording and encourages deeper understanding of the problem.

---

## Pattern Recognition

The AI analyzes logged solution approaches and identifies the primary DSA pattern being used.

Examples include:

* Sliding Window
* Two Pointers
* Binary Search
* Depth First Search
* Breadth First Search
* Dynamic Programming
* Greedy
* Backtracking

This allows future categorization and filtering of questions by pattern.

---

## Recall Evaluation

During practice sessions, users submit their remembered approach to a problem.

The AI compares the recalled explanation with the originally logged approach and generates:

* Recall score
* Missing concepts
* Correct concepts
* Improvement suggestions

The purpose is to evaluate understanding rather than correctness of code.

---

## Practice History

Every practice attempt is recorded.

This creates a historical record of:

* Recall performance
* Improvement over time
* Frequently forgotten concepts
* Areas requiring additional review

---

## Spaced Repetition Support

Future versions of the system will introduce spaced repetition scheduling.

Questions that are frequently forgotten can be reviewed more often, while questions that are consistently remembered can appear less frequently.

This helps optimize learning efficiency.

---

# Technical Architecture

The application follows a layered architecture:

Frontend

↓

FastAPI Backend

↓

Service Layer

↓

SQLAlchemy ORM

↓

SQLite / PostgreSQL

↓

AI Services (VibeThinker-3B)

The architecture is intentionally modular to allow future expansion without major restructuring.

---

# Artificial Intelligence Integration

The application uses the VibeThinker-3B model through HuggingFace Transformers.

The model is responsible for:

* Question rephrasing
* Pattern extraction
* Recall evaluation
* Feedback generation

The AI layer is used only for tasks requiring reasoning and language understanding.

Database operations, scheduling, and business logic remain deterministic and are handled by the backend.

---

# Technology Stack

## Backend

* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn

## Database

Development:

* SQLite

Production:

* PostgreSQL

## AI

* HuggingFace Transformers
* VibeThinker-3B

## Configuration

* python-dotenv

---

# Design Principles

The project follows several guiding principles:

### Learning Over Solving

The goal is not to solve more problems but to remember more patterns.

### Active Recall

Users should retrieve knowledge from memory instead of rereading solutions.

### Explain Approaches, Not Code

The system emphasizes reasoning and strategy rather than implementation details.

### AI as an Assistant

AI enhances learning through evaluation and rephrasing but does not replace the learning process itself.

### Incremental Improvement

The platform is designed to evolve from a simple logging and practice system into a comprehensive memory reinforcement tool.

---

# Expected Outcome

By consistently logging and reviewing solved problems, users should be able to:

* Retain DSA concepts longer
* Improve pattern recognition
* Recall approaches more quickly
* Identify weak areas of understanding
* Build a durable knowledge base of solved problems

The application serves as a personalized memory system for DSA preparation rather than a traditional coding platform.
