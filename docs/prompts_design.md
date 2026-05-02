# Prompt Design Guide

## Design Principles

1. **Role-specific personas**: Each agent has a distinct Chinese internet persona
2. **Structured output**: All prompts request JSON or structured text output
3. **Chinese-native**: Prompts are written in Chinese to match target audience
4. **Viral gene injection**: Content creation prompts embed viral content patterns

## Prompt Organization

- `core/prompts/shared/` -- Reusable prompt fragments (KOC persona, viral hooks)
- Agent-specific prompts are embedded in each agent's module

## KOC Persona System

Each content piece is written from a KOC (Key Opinion Consumer) perspective:
- Technical depth with accessible language
- Platform-specific tone adaptation
- Strategic use of hooks and emotional triggers

## Chinese Viral Content Patterns

Key patterns encoded in `chinese_hooks.py`:
- Information asymmetry (readers learn something new)
- Emotional resonance (curiosity, urgency, excitement)
- Practical value (immediately actionable)
- Social currency (worth sharing)
- Controversy (room for discussion)
