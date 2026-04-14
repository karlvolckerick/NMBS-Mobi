# Use VoiceLive with Noise Suppression

* **Status:** accepted
* **Proposer:** @lherold
* **Date:** 2026-01-27

## Context and Problem Statement

The AI Contact Centre Solution Accelerator handles voice interactions with users from diverse environments. The choice
of voice model and API is critical to ensure high performance in function call execution under varying noise conditions.

This ADR documents the selection of VoiceLive with Noise Suppression as the default voice processing configuration for
the accelerator, based on systematic evaluation of available options.

## Decision Drivers

* Function Calling Success Rate - Users must successfully complete multi-turn function call sequences
* Function Call Recall - Accurate execution of backend functions based on voice commands
* Noise Robustness - Performance must remain acceptable across various noise conditions
* Production Reliability - Minimize conversation faults and unexpected behavior
* Scalability - Ability to handle production traffic volumes
* Cost Efficiency - Token-based pricing model alignment with usage patterns

## Considered Options

* VoiceLive with Noise Suppression (VLWN)
* GPT Realtime with Near Field Noise Suppression (GPTWNNF)
* GPT Realtime with Far Field Noise Suppression (GPTWNFF)
* VoiceLive without Noise Suppression (VLNN)
* GPT Realtime without Noise Suppression (GPTNN)
* Custom Solution with Silero VAD

## Decision Outcome

Chosen option: "VoiceLive with Noise Suppression (VLWN)", because it achieves the highest average function calling
success rate across all noise conditions, with statistically significant advantages in high-noise environments. For
moderate noise deployments, GPT Realtime with Near Field Noise Suppression is an acceptable alternative with comparable
performance.

## Experimentation

To inform this decision, systematic experiments were conducted comparing each option across multiple noise conditions. 
The test scenarios included:

* **Noise Conditions**: Silent, Light Cafe, Medium Cafe, Loud Cafe, Heavy Cafe
* **Metrics Measured**: Function calling success rate, function call recall, conversation turns, fault rate, handoff 
  success rate, automation success rate
* **Statistical Analysis**: Confidence intervals calculated for key metrics, with statistical significance testing 
  (p < 0.05) for comparisons between options

The results below reflect aggregated performance across all test conditions unless otherwise specified.

## Pros and Cons of the Options

### VoiceLive with Noise Suppression (VLWN)

Uses Microsoft's `azure_deep_noise_suppression` model.

* Good, because it achieves highest average function calling success rate (89.2% across all noise conditions)
* Good, because statistically significant advantage in high-noise: +13.0% in Loud Cafe [+1.8%, +24.2%], +15.9% in Heavy
  Cafe [+7.2%, +24.6%] compared to GPTWNNF
* Good, because it has the lowest fault rate across conditions (124 total faults across conditions)
* Good, because it achieves highest automation success rate (79.9% average)
* Bad, because it requires more conversation turns on average (9.5 vs 8.0 for GPTWNNF)
* Bad, because it has slightly lower handoff success rate (77.7% vs 84.4%)

### GPT Realtime with Near Field Noise Suppression (GPTWNNF)

Optimized for close-talking microphones (headphones, mobile devices).

* Good, because it achieves second-best function calling success rate (81.6% average)
* Good, because it has the most efficient conversations 8.0 average turns)
* Good, because it has strong performance in moderate noise conditions (94.4% in Medium Cafe)
* Good, because it has the highest function call recall (85.3% average)
* Bad, because it performs significantly worse in high-noise conditions vs VLWN
* Bad, because it has more total faults than VLWN (12% more than VLWN)

### GPT Realtime with Far Field Noise Suppression (GPTWNFF)

Optimized for distant microphones (laptop mics, conference rooms).

* Good, because it improves over no noise suppression (66.7% average function calling success)
* Good, because it has efficient conversations (8.2 turns average)
* Bad, because it is significantly worse than both VLWN and GPTWNNF across all conditions
* Bad, because it has higher fault rate (164 total faults)

### VoiceLive without Noise Suppression (VLNN)

* Good, because it is the simplest configuration
* Good, because it has highest handoff success rate (85.6%)
* Bad, because it has poor function calling success in noisy environments (53.2% in high noise)
* Bad, because it requires high conversation turns (10.4 turns average)
* Bad, because it has high fault rate (207 total faults)

### GPT Realtime without Noise Suppression (GPTNN)

* Good, because it has efficient conversations (8.3 turns average)
* Bad, because it has worst function calling performance (50.7% success rate)
* Bad, because it shows no improvement over VLNN baseline in noisy conditions
* Bad, because it has high fault rate (210 total faults)

### Custom Solution with Silero VAD

Build a custom pipeline using [Silero VAD](https://github.com/snakers4/silero-vad) for voice activity detection with
separate STT/TTS components. Explicitly not considered in experiments, as implementation effort not feasible with on top
of comparison with GPTRealtime and VoiceLive.

## VoiceLive Benefits

### Key Benefits

| Benefit                        | Description                                                                           |
|--------------------------------|---------------------------------------------------------------------------------------|
| Unified API                    | Single interface for STT, LLM, and TTS eliminates orchestration complexity            |
| Low Latency                    | End-to-end optimization reduces perceived latency vs. chained components              |
| Noise Suppression              | Built-in `azure_deep_noise_suppression` with proven improvement in noisy environments |
| Echo Cancellation              | Prevents agent from picking up its own responses                                      |
| Advanced End-of-Turn Detection | Context-aware detection allows natural pauses without premature cutoff                |
| 140+ Locales                   | Broad language coverage                                                               |
| 600+ Standard Voices           | Extensive voice options across many languages                                         |

### British English Voice Support (depending on selected Voice Live Model)

Based
on [Voice live API language support - Foundry Tools | Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-language-support?tabs=speechoutput)
Azure Voice Live supports multiple British English (`en-GB`) voices. The following voices are available (as of Jan.
2026 - [https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#:~:text=en%2DGB,ThomasNeural%20(Male)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#:~:text=en%2DGB,ThomasNeural%20\(Male\)) ):

|         |                          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|---------|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `en-GB` | English (United Kingdom) | `en-GB-SoniaNeural` (Female)  <br>`en-GB-RyanNeural` (Male)  <br>`en-GB-LibbyNeural` (Female)  <br>`en-GB-AdaMultilingualNeural`4 (Female)  <br>`en-GB-OllieMultilingualNeural`4 (Male)  <br>`en-GB-AbbiNeural` (Female)  <br>`en-GB-AlfieNeural` (Male)  <br>`en-GB-BellaNeural` (Female)  <br>`en-GB-ElliotNeural` (Male)  <br>`en-GB-EthanNeural` (Male)  <br>`en-GB-HollieNeural` (Female)  <br>`en-GB-MaisieNeural` (Female, Child)  <br>`en-GB-NoahNeural` (Male)  <br>`en-GB-OliverNeural` (Male)  <br>`en-GB-OliviaNeural` (Female)  <br>`en-GB-ThomasNeural` (Male) |

Multilingual voices (Ada, Ollie) can auto-detect language or be configured with British accent using SSML
`<lang xml:lang="en-GB">` [see [Voice and sound with Speech Synthesis Markup Language (SSML) - Speech service - Foundry Tools | Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice#lang-examples)]

### Scalability

VoiceLive is a managed service with the following documented constraints:

| Metric                     | Limit         | Adjustable?                   |
|----------------------------|---------------|-------------------------------|
| New connections per minute | 30 (Default)  | Yes (Standard S0 Tier only)   |
| Tokens per minute          | <= 120,000    | Auto-adjusts with connections |
| Max connection length      | <= 60 minutes | No                            |

**Best Practices:**

* **Gradual Ramp-up:** The service requires time to autoscale. Avoid sharp traffic spikes (e.g., increasing load 4x in
  one second).
    * _Recommended Pattern:_ Start with ~20 concurrent connections. Increase by 20 connections every 90-120 seconds.
    * _Handling Throttling:_ If 429 (Too Many Requests) errors occur, back off and retry with increasing intervals (
      1-2-4
      minutes).
* **Retry Logic:** The application must implement retry logic to handle 429 errors, which may occur during normal
  autoscaling operations.
* **Multi-Region Deployment:** For high volume processing exceeding region capacity, distribute workload across
  resources in different Azure regions. **Multiple resources in the _same_ region share backend capacity and do not
  improve scalability.**

### Production Readiness

* 10+ Azure regions supported
* SDKs available for Python and C#
* Content filtering included by default
* Telephony integration via Azure Communication Services available

### Cost Analysis

Based
on [Voice Live API Overview - Foundry Tools | Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live#pricing).
There’s three different tiers - our experiments used “gpt-realtime” hence we are in the “Pro” tier.

### Pricing Tiers (Effective July 1, 2025)

|           |                                                          |                             |
|-----------|----------------------------------------------------------|-----------------------------|
| **Tier**  | **Models**                                               | **Use Case**                |
| **Pro**   | gpt-realtime, gpt-4o, gpt-4.1, gpt-5, gpt-5-chat         | High accuracy requirements  |
| **Basic** | gpt-realtime-mini, gpt-4o-mini, gpt-4.1-mini, gpt-5-mini | Balanced cost/performance   |
| **Lite**  | gpt-5-nano, phi4-mm-realtime, phi4-mini                  | Cost-sensitive applications |

### Token Estimation

|                  |                        |                         |
|------------------|------------------------|-------------------------|
| **Model Family** | **Input (tokens/sec)** | **Output (tokens/sec)** |
| Azure OpenAI     | ~10                    | ~20                     |
| Phi models       | ~12.5                  | ~20                     |

### Cost Drivers

1.**Audio duration**: Primary cost factor - tokens scale with audio length
2.**Conversation turns**: VLWN averages 9.5 turns vs GPTWNNF 8.0 turns
3.**Cached context**: Prompt and conversation history are also billed
4.**Custom voice/avatar**: not applicable

### Comparison

|                    |                         |                                |                          |
| ------------------ | ----------------------- | ------------------------------ | ------------------------ |
| **Model**          | **Input ($/1M tokens)** | **Cached Input ($/1M tokens)** | **Output ($/1M tokens)** |
| **Voice Live Pro** | $44.00                  | $2.75                          | $88.00                   |
| **GPT Realtime**   | $32.00                  | $0.40                          | $64.00                   |


## Links

* [Azure OpenAI Realtime Audio Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/realtime-audio-reference)
* [Voice Live API Reference](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-api-reference)
* [Voice Live Overview](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live)
* [Speech Service Quotas and Limits](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits)
* [Speech Services Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services)
* [Voice Live FAQ](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-faq)
* [Voice Live Language Support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-language-support)
