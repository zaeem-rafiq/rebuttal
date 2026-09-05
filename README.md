# Rebuttal

> A Strands agent that answers Stripe chargebacks the way an owner would, and texts the owner only when it shouldn't decide alone.

Built for the **Agents for Humans** hackathon (Professional Agents track).

## Overview
Rebuttal defends against fraudulent and invalid payment disputes automatically using AWS Bedrock AgentCore and Strands Agents SDK, pulling order/shipping context, assembling evidence packages, submitting rebuttals via Stripe API, and escalating ambiguous decisions to the store owner via SMS with human-in-the-loop interrupts.
