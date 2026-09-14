# Complete narration for voice generation approval

Destination: Microsoft Edge TTS, using the existing Andrew multilingual English voice.
Payload: only the nine public-intended narration paragraphs below. No raw records, personal names, addresses, Stripe object IDs, or pending scores are included.
Scenes 1 and 2 already have matching cached audio. Remaining narration can be generated after approval for this complete text and destination.
Recorded-result scenes remain contingent on verified final visuals; this script does not supply their values.

## Scene 1: 01 / THE PROBLEM

For small online merchants, a chargeback starts a race to assemble records. The order, delivery history, customer messages, and response policy sit in different places. Rebuttal brings those records together, recommends a response, and drafts evidence for review. The goal is less manual case assembly, with the merchant retaining control of consequential decisions.

## Scene 2: 02 / HOW IT WORKS

Rebuttal uses the AWS Strands Agents SDK. After intake, four agents collect evidence in parallel. Strategy waits for all four. The drafter then receives both the evidence and the proposed response. A separate executor uses an approval hook before taking a guarded action.

## Scene 3: 03 / RECORDING SETUP

The next scenes replay a recorded local run. The merchant records are synthetic, and the Stripe objects are in test mode. The screen is an edited presentation of captured output, so reveals follow the narration rather than the original wait times. The owner response comes through the developer command line.

## Scene 4: 04 / RETRIEVED FACTS

The recorded run begins with a Stripe test dispute. The panel shows selected facts retrieved for that case: the order, delivery record, customer communications, and merchant policy. The execution trace shows the Strands graph moving through collection, strategy, and drafting. These excerpts come from the captured local run.

## Scene 5: 05 / STRATEGY AND DRAFT

Next, compare the proposed strategy with the records that support it. The recommendation and draft are shown separately. Read the evidence excerpt alongside the retrieved facts. Missing evidence and uncertainty must remain visible, and a proposed action must stay distinct from a completed action.

## Scene 6: 06 / THE OWNER DECISION

The approval step is a deliberate decision point. In this recording, the developer command line stands in for the merchant interface. Fight, concede, and hold are the three available responses. The selected response is passed back to the Strands interrupt, after which the recorder checks Stripe again. Phone notification delivery is disabled for this local demonstration.

## Scene 7: 07 / APPROVAL AND READBACK

Here is the approval interrupt and the developer command line response. The display preserves the recorded choice and the guarded action count. After resuming, the recorder reads Stripe again. Compare the before and after states. That readback establishes the test result, not a real-world dispute outcome.

## Scene 8: 08 / VALIDATION

The validation panel identifies the source revision and the checks that ran against it. It shows the unit test result alongside the fixed synthetic-case evaluation, covering action, approval, expected value, and grounding. Read the observed results and thresholds together. This benchmark does not measure real merchant recovery rates.

## Scene 9: 09 / WHAT THIS DEMONSTRATES

Rebuttal gives small merchants a place to review the facts, the proposed response, and the next action. This prototype runs locally with synthetic merchant data and Stripe test objects. Real merchant outcomes and live phone delivery remain outside this demonstration. The goal is a clearer, more controlled dispute workflow.
