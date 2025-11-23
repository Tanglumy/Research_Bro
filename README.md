
# Research Copilot: End-to-End Workflow & System Design

## 1. Overview

**Goal:**
Build an AI “research copilot” that takes a researcher from a fuzzy, natural-language idea to:

* A clear view of the **existing literature & gaps**
* A set of **structured, testable hypotheses**
* A **concrete experimental design**
* A large set of **balanced experimental stimuli**
* **Synthetic data** from simulated participants to sanity-check the design

…all in one continuous workflow.

The system is organized into five capability modules:

1. Literature Landscape Explorer
2. Hypothesis Generator & Structurer
3. Experimental Design Builder & Critic
4. Stimulus Factory
5. Synthetic Participant Simulator

These modules are orchestrated in a single workflow, but each module can also be used independently.

---

## 2. Target Users & Scope

**Primary users**

* Early-career researchers (PhD students, postdocs)
* Supervisors / PIs exploring new lines of research
* Research assistants involved in experimental design and material generation

**Discipline focus (initially)**

* Psychology, cognitive science, behavioral sciences, and related areas where:

  * Research questions can be expressed in fairly structured terms
  * Experiments often involve **manipulations, vignettes, self-report measures, and quantitative analysis**

---

## 3. End-to-End Workflow

### 3.1 High-Level Workflow

1. **Input Research Idea**

   * User types a natural language question, or pastes paper links / abstracts.
   * System parses it into candidate constructs, domains, and potential relationships.

2. **Literature Landscape (Module 1)**

   * System identifies:

     * Relevant **theoretical frameworks**
     * Typical **operationalizations** and **measures**
     * Common **experimental paradigms / tasks**
     * **What has been done** vs. **what is missing**
   * Visualized as a **concept graph** + structured lists.

3. **Hypothesis Generation (Module 2)**

   * Using the landscape + user intent:

     * Extracts candidate **IVs, DVs, mediators, moderators**
     * Proposes **multiple structured hypotheses**
     * Outputs machine-readable representation (e.g., JSON) + human-readable summary.

4. **Experiment Design (Module 3)**

   * From selected hypotheses:

     * Proposes **design type** (between / within / mixed)
     * Suggests **conditions**, **measures**, **time points**
     * Flags **confounds and design pitfalls**
     * Suggests **rough sample size ranges**
     * Generates a draft **Methods section**.

5. **Stimulus Generation (Module 4)**

   * From design specs:

     * Generates large sets of **scenarios / dialogues / self-talk snippets**, etc.
     * Annotates each stimulus with **metadata** (valence, intensity, relationship type…)
     * Balances across conditions and languages.

6. **Synthetic Participant Simulation (Module 5)**

   * Creates a set of **persona templates** (e.g., high anxiety, secure attachment, different cultures).
   * Simulates responses for a chosen sample size and persona mix.
   * Outputs:

     * Condition means, SDs, and rough effect directions
     * “Dead” variables (no variation) and weak manipulations
     * Example free-text responses for inspection.

7. **Export & Integration**

   * The user can export:

     * Knowledge graph slices + citations
     * Hypothesis tables / JSON
     * Design tables + Methods draft
     * Stimulus banks + metadata
     * Synthetic result summaries

---

## 4. System Architecture

### 4.1 Core Components

* **Frontend**

  * Left: Chat / command interface
  * Right: Interactive **Knowledge Graph Panel**
  * Additional views:

    * Hypothesis table view
    * Design matrix view
    * Stimulus editor
    * Simulation dashboard

* **Backend**

  * **Orchestrator**:

    * Manages workflow across the five modules
    * Maintains a shared **Project State** (concepts, hypotheses, designs, stimuli, simulation results)
  * **Module Services**:

    * Each core capability is implemented as a separate service (or agent):

      1. Literature Explorer
      2. Hypothesis Engine
      3. Design Engine
      4. Stimulus Engine
      5. Simulation Engine
  * **Data Layer**:

    * Graph database for concepts & relations
    * Document store for paper metadata & full texts
    * Relational / JSON store for hypotheses, designs, stimuli, simulated data

---

## 5. Shared Data Model (Conceptual)

To allow smooth transitions between modules, we define a few shared data types.

### 5.1 Research Question Object

```json
{
  "id": "rq_001",
  "raw_text": "user's natural language input",
  "parsed_constructs": ["construct_A", "construct_B"],
  "domain": "e.g. social relationships, emotion regulation",
  "notes": "any extra constraints or context"
}
```

### 5.2 Concept & Knowledge Graph Nodes

Each concept (e.g., “shame”, “emotion regulation”) is a node:

```json
{
  "id": "concept_123",
  "label": "Emotion Regulation",
  "type": "theoretical_construct",
  "linked_papers": ["paper_abc", "paper_def"],
  "common_measures": ["ERSQ", "ERQ"],
  "operationalizations": [
    {
      "description": "writing task manipulating reappraisal vs rumination",
      "typical_DVs": ["state negative affect", "self-compassion"]
    }
  ]
}
```

Edges represent relationships:

```json
{
  "source": "concept_123",
  "target": "concept_456",
  "relation_type": "predicts" | "associated_with" | "operationalized_by" | ...
}
```

### 5.3 Hypothesis Object

```json
{
  "id": "hypothesis_01",
  "text": "Plain English hypothesis",
  "iv": ["IV_01"],
  "dv": ["DV_01", "DV_02"],
  "mediators": ["M_01"],
  "moderators": ["Mod_01"],
  "theoretical_basis": [
    "concept_123",
    "paper_abc"
  ],
  "expected_direction": "e.g. IV_01 (condition A > condition B) reduces DV_01"
}
```

### 5.4 Experiment Design Object

```json
{
  "id": "design_01",
  "design_type": "between_subjects | within_subjects | mixed",
  "conditions": [
    {
      "id": "cond_01",
      "label": "Condition A",
      "manipulation_description": "..."
    }
  ],
  "measures": [
    {
      "id": "measure_01",
      "label": "State anxiety",
      "scale": "STAI-S",
      "time_points": ["baseline", "post"]
    }
  ],
  "sample_size_plan": {
    "assumed_effect_size": "small | medium | large",
    "per_condition_range": [40, 60]
  },
  "confound_notes": [
    "Potential confound: manipulation length differs across conditions."
  ]
}
```

### 5.5 Stimulus Item Object

```json
{
  "id": "stim_001",
  "text": "Stimulus text",
  "language": "en",
  "metadata": {
    "valence": "negative | mixed | neutral",
    "relationship_type": "friend | partner | coworker",
    "intensity": "low | medium | high",
    "ambiguity_level": "low | medium | high",
    "assigned_condition": "cond_01"
  },
  "variants": [
    {
      "id": "stim_001_v1",
      "variant_type": "original",
      "text": "..."
    },
    {
      "id": "stim_001_v2",
      "variant_type": "manipulation_version_A",
      "text": "..."
    }
  ]
}
```

### 5.6 Synthetic Participant Object

```json
{
  "id": "sp_001",
  "persona": {
    "attachment_style": "avoidant",
    "self_criticism": "high",
    "culture": "collectivistic",
    "other_traits": {}
  },
  "responses": [
    {
      "stimulus_id": "stim_001",
      "condition_id": "cond_01",
      "dv_scores": {
        "DV_01": 3.2,
        "DV_02": 4.5
      },
      "open_text": "simulated free-text response"
    }
  ]
}
```

---

## 6. Module Specs

### 6.1 Module 1: Literature Landscape Explorer

**Input**

* ResearchQuestion object (or raw text)
* Optional: list of seed papers / DOIs / abstracts

**Core Functions**

1. **Concept Extraction & Mapping**

   * Parse key constructs, populations, and contexts.
   * Map them to existing nodes in the concept graph; create new nodes if needed.

2. **Literature Retrieval & Structuring**

   * Retrieve relevant papers.
   * Organize into:

     * Theoretical frameworks
     * Operationalizations & measures
     * Experimental tasks / paradigms
     * Populations, cultures, and contexts used

3. **Gap Identification**

   * Compare current question with:

     * Existing combinations of IVs/DVs
     * Existing populations and settings
   * Produce a **“gap summary”**: what has not been systematically tested.

**Output**

* Updated concept graph (nodes + edges)
* Structured lists:

  * Theoretical frameworks
  * Measures & operationalizations
  * Experimental paradigms
  * Research gaps
* Human-readable summary + citations

**UI**

* Right panel: interactive graph

  * Clicking a node shows:

    * Representative papers
    * Typical operationalizations
    * Common measures

---

### 6.2 Module 2: Hypothesis Generator & Structurer

**Input**

* ResearchQuestion object
* Selected concepts/frameworks from Module 1
* Optional: user constraints (e.g., “I care about cross-cultural differences”)

**Core Functions**

1. **Concept Decomposition**

   * Identify potential IVs, DVs, mediators, moderators.

2. **Hypothesis Proposal**

   * Generate multiple hypotheses with:

     * Plain language statement
     * Structured roles (IV, DV, etc.)
     * Expected direction
     * Theoretical justification

3. **Machine-Readable Representation**

   * Export hypotheses as JSON / table for later modules.

**Output (example structure)**

A table of hypotheses:

| Hypothesis ID | IV(s) | DV(s) | Mediator(s) | Moderator(s) | Direction | Theory Basis |
| ------------- | ----- | ----- | ----------- | ------------ | --------- | ------------ |

Plus the full JSON objects.

---

### 6.3 Module 3: Experimental Design Builder & Critic

**Input**

* Selected hypotheses (from Module 2)
* Constraints: lab resources, online vs in-person, sample type, etc.

**Core Functions**

1. **Design Proposal**

   * Suggest design type (between/within/mixed).
   * Define conditions, manipulation structure, and measurement time points.

2. **Confound & Validity Checker**

   * Check:

     * Whether manipulations unintentionally change other factors (length, tone).
     * Order effects and need for counterbalancing.
     * Sampling limitations (e.g., only students).

3. **Power / Sample Size Heuristic**

   * Provide indicative N ranges for small/medium/large effects.

4. **Method Section Draft**

   * Auto-generate:

     * Participants
     * Design
     * Materials
     * Procedure
   * Written in journal-ready narrative, but editable by user.

**Output**

* ExperimentDesign object
* Condition × measurement matrix, e.g.:

| Condition ID | Description | Measures | Time Points | Notes |

* Draft Methods text.

---

### 6.4 Module 4: Stimulus Factory

**Input**

* ExperimentDesign object
* User-specified parameters:

  * Scenario types, relationship roles, intensity, ambiguity, languages, style (chat, diary, monologue, etc.)
* Desired number of stimuli (e.g., 50–200)

**Core Functions**

1. **Stimulus Generation**

   * Generate scenario texts and associated self-talk / dialogue.
   * Ensure systematic variation along specified dimensions.

2. **Metadata Annotation**

   * Label each stimulus with:

     * Valence
     * Relationship type
     * Intensity
     * Ambiguity level
     * Assigned condition, etc.

3. **Balancing & Filtering**

   * Balance distributions across conditions.
   * Filter out:

     * Ethically problematic content
     * Overly extreme or implausible scenarios

4. **Translation & Semantic Equivalence**

   * Generate multi-language versions.
   * Aim for **conceptual equivalence** rather than literal translation.

**Output**

* StimulusItem objects (with variants and metadata)
* Summaries:

  * Metadata distributions
  * Example stimuli for human review

---

### 6.5 Module 5: Synthetic Participant Simulator

**Input**

* ExperimentDesign object
* Stimulus sets
* Persona templates + sample plan:

  * e.g., “200 participants, 50 each of 4 attachment styles”

**Core Functions**

1. **Persona Modeling**

   * Define latent profiles with:

     * Personality traits
     * Attachment style
     * Self-esteem / self-criticism
     * Cultural background etc.

2. **Response Simulation**

   * For each simulated participant:

     * Assign to conditions per design
     * Generate DV scores (e.g., Likert ratings)
     * Optionally generate open-ended text

3. **Result Aggregation & Diagnostics**

   * Compute:

     * Means, SDs, rough effect estimates per condition
     * Variables with low variance or no condition differences
     * Conditions with minimal separation (weak manipulations)

4. **Qualitative Inspection**

   * Produce example simulated responses for human inspection.

**Output**

* SyntheticParticipant objects
* Summary tables:

  * Condition × DV means/SDs
  * Effect direction indicators
* Diagnostic report: what looks too weak/too strong/ill-posed.

---

## 7. UX Flow Summary

From the researcher’s point of view:

1. **Start a Project**

   * Input a research idea (text / paper).
   * System returns concept graph + literature landscape.

2. **Refine & Select**

   * Click through concepts, read summaries, mark interesting paths.
   * Select key constructs → trigger hypothesis generation.

3. **Generate Hypotheses**

   * View multiple hypotheses, edit them, pin the ones to pursue.

4. **Build Design**

   * Ask the system to propose a design for selected hypotheses.
   * Inspect design table + Methods draft; iterate as needed.

5. **Generate Stimuli**

   * Specify desired scenario properties.
   * Review sample stimuli and metadata; accept / edit.

6. **Run Simulation**

   * Choose persona mix and sample size.
   * Inspect simulated results & example responses.

7. **Export**

   * Export everything needed:

     * For preregistration / registered reports
     * For supervisor meetings
     * For actual implementation in survey/experiment platforms

---

If you’d like, next step we can:

* Turn this into a **short “product spec”** for engineers, or
* Zoom into one module (e.g. Literature Explorer) and design its **internal prompts + APIs** in more detail.

YOU MUST USE the SpoonOS workflow to design the workflow.
here is the docs: https://xspoonai.github.io/docs/getting-started/quick-start/