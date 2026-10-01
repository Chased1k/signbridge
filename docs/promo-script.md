# SignBridge — Promo Script (Proof of Concept Voice Note)

**Purpose:** Read this as a voice note / talking point script to introduce SignBridge.
Tone: conversational, authentic, excited but not hype-y. Like you're explaining
to a smart friend over coffee.

---

## The Hook (10 sec)

So I've been building something that takes my voice notes — like, me just
rambling into my phone — and turns them into a video of a person signing
in American Sign Language.

## The Problem (20 sec)

There are millions of deaf and hard-of-hearing people who use ASL as their
primary language. And the amount of content being created every day —
podcasts, voice notes, video content, courses — that is completely
inaccessible to them is staggering.

Existing translation tools are either text-to-text (not sign language),
or they're stick-figure avatars that look terrible and have no facial
expression, which is a huge part of ASL grammar. Or they're human
interpreters, which doesn't scale.

## What We're Building (30 sec)

SignBridge is a pipeline that takes audio in and produces a photorealistic
video of an ASL signer performing that translation. Here's how it works:

1. **Audio goes in** — a voice note, a podcast clip, any spoken content
2. **Whisper transcribes it** to text
3. **An LLM translates** that English text into ASL gloss — which is the
   written notation system for sign language
4. **We look up each sign** in a database of 2,700+ real ASL signs recorded
   by native signers at Boston University
5. **We extract the body pose** from those recordings — the skeleton,
   the hand shapes, the movement path
6. **We stitch those poses together** into a continuous signing sequence
7. **Then we run it through an AI video model** — like fal.ai's Dreamactor —
   to render it as a photorealistic human signer with facial expressions

The result: you ramble into your phone, and minutes later you have a
video of someone signing your message. Like a real interpreter, but
on-demand and infinitely scalable.

## Why This Is Different (20 sec)

The key insight is that we're not trying to generate sign language from
scratch with AI — that produces garbage. We're using real human recordings
from a university dataset as the motion source, then using AI only for the
final visual polish. The signing is real. The expressions are real. The
AI just makes it look good instead of looking like a video game character.

And the coverage loop — if a word isn't in our database, the LLM rephrases
it using signs we do have. "Procrastinate" becomes "PUT-OFF." If we still
can't find it, we fingerspell it. The system gets smarter over time as we
identify and fill vocabulary gaps.

## The Market (15 sec)

This isn't just a cool tech demo. The ADA requires accessibility for a lot
of content. Sign language interpretation services are a multi-billion dollar
market. Every school, every government agency, every content creator who
wants to reach the deaf community needs this. And right now, the options
are either expensive human interpreters or bad avatars.

## Where We Are (15 sec)

Right now we're in proof-of-concept mode. We've downloaded the dataset,
we're processing the pose library on a GPU server, and we're building the
pipeline to take a voice note all the way through to a finished video.
The first working demo should be ready in days, not months.

## The Ask (10 sec)

If you know anyone in the deaf community, in accessibility, or in content
creation who might want to see this — or if you just want to try it
yourself — let me know. We're looking for early feedback and test cases.

---

**Total: ~2 minutes spoken**

**Tips for recording:**
- Don't read it word-for-word — use it as a guide, speak naturally
- Pause between sections for emphasis
- The "Why This Is Different" section is the most important — nail that one
- If doing as a video, show the dashboard (signbridge.wdfab.io) while talking
- End with a question, not a statement — invite conversation