# Marketing-Intelligent-Agent

A Streamlit-based creator intelligence prototype for marketing campaign
planning. The application evaluates Instagram creators using
performance, semantic relevance, and brand-compatibility evidence, ranks
the strongest recommendations, and produces creator-specific content
briefs.

## Features

-   Evaluates a 20-creator Instagram sample using the available creator,
    post, audience, and advertising data.
-   Combines performance, campaign relevance, and brand compatibility
    into a transparent weighted score.
-   Produces five differentiated creator recommendations.
-   Generates evidence-grounded creative briefs for shortlisted
    creators.
-   Maintains a persistent, deduplicated brand-memory store.
-   Supports optional Gemini or Groq integration; deterministic
    fallbacks keep the prototype usable without an API key.

## Setup

### Requirements

-   Python 3.10 or newer
-   pip

### Installation

1.  Open a terminal in the project directory.

2.  Install the dependencies:

    ``` bash
    pip install -r requirements.txt
    ```

3.  Confirm that the required CSV files are present in the `data/`
    directory.

4.  If the files are stored elsewhere, update the corresponding entries
    under `data_paths` in `config.json`.

5.  To enable an optional language-model provider, copy `.env.example`
    to `.env`, select `gemini` or `groq` in `config.json`, and add the
    relevant API key. Keep `.env` private and do not commit it to
    version control.

### Run the application

``` bash
streamlit run app.py
```

The app can run without an external LLM API key. In that mode, it uses
deterministic explanations and content-brief fallbacks.

## Project structure

  -----------------------------------------------------------------------
  Module                              Responsibility
  ----------------------------------- -----------------------------------
  `app.py`                            Streamlit application entry point
                                      and user interface.

  `data_loader.py`                    Loads configured CSV files,
                                      validates expected columns, and
                                      reports data-quality issues.

  `performance_evaluator.py`          Compares creator post performance
                                      using relative metrics and
                                      cross-creator percentiles.

  `semantic_evaluator.py`             Measures relevance between creator
                                      evidence, campaign briefs, and
                                      advertising creative context using
                                      sentence embeddings or a lexical
                                      fallback.

  `brand_evaluator.py`                Evaluates brand compatibility,
                                      natural-integration considerations,
                                      available audience evidence, and
                                      review flags.

  `brand_memory.py`                   Stores deduplicated brand, creator,
                                      and creative evidence for reuse.

  `decision_agent.py`                 Combines evaluator outputs using
                                      configurable weights and selects
                                      recommendation roles.

  `creative_generator.py`             Creates creator-specific content
                                      briefs grounded in available
                                      evidence.

  `llm_client.py`                     Provides optional Gemini/Groq
                                      integrations.

  `config.json`                       Contains data paths, scoring
                                      weights, and application settings.

  `data/`                             Contains the CSV datasets used by
                                      the application.

  `outputs/`                          Stores generated evaluations,
                                      recommendations, and brand memory.
  -----------------------------------------------------------------------

## Evaluation approach

The default scoring weights are:

  Evidence layer          Weight
  --------------------- --------
  Performance                35%
  Semantic fit               40%
  Brand compatibility        25%

These weights are configurable in `config.json`. They are heuristic
judgement weights, not coefficients trained on historical campaign
outcomes.

The performance layer compares creators within the available sample
using measures such as median plays, visible engagement, share rate, and
consistency. The semantic layer assesses how closely available creator
and content evidence matches the campaign brief. The brand layer
considers natural integration and the brand-safety information available
in the supplied data.

The final score is a comparative suitability indicator. It is not a
probability of campaign success, a sales forecast, or a guaranteed
performance result.

## Recommendation output

The decision agent aims to return five distinct recommendations:

1.  The highest-ranked creator based on the combined score.
2.  The strongest performance-led alternative.
3.  The strongest semantic-fit alternative.
4.  The next-best overall creator.
5.  The following eligible overall creator.

Duplicate creators are skipped when assigning recommendation roles.

## Data interpretation and limitations

-   Advertising spend, impressions, views, clicks, carts, purchases, and
    revenue fields in the supplied advertising dataset are synthetic
    exercise data. Any derived CTR, conversion, or ROAS values are
    descriptive exercise analysis only.
-   Organic creator-post plays and engagement are not paid campaign
    outcomes and must not be presented as paid ROAS or as a forecast of
    paid campaign performance.
-   Audience demographic information is available for only a subset of
    the creators. Missing demographic data is marked unavailable rather
    than inferred from a creator's identity or content.
-   Automatically generated labels, including hook type, format, child
    presence, and topic, may be inaccurate. Review the original posts
    and ads before relying on these labels.
-   Some creators may hide likes. A zero or low visible like count
    should not automatically be interpreted as zero engagement.
-   Creator-level recommendations are limited by the coverage and
    quality of the supplied data. Missing evidence should remain unknown
    rather than being fabricated.
-   Product efficacy, health, and nutrition claims must use approved
    brand wording. If no approved claims are configured, generated
    concepts should avoid efficacy claims.
-   Keyword or brand-safety flags are prompts for human review, not
    legal or regulatory conclusions.

## Generated files

After a successful run, the application writes its generated results to
`outputs/`, including:

-   `creator_evaluations.csv` --- evaluation results for the creator
    sample.
-   `top_five.csv` --- ranked recommendation summary.
-   `top_five.json` --- structured recommendation output.
-   `brand_memory.json` --- persistent, deduplicated evidence memory.

The exact files produced depend on the application configuration and
execution path.

## Optional language-model configuration

Gemini and Groq integrations are optional. Configure the provider in
`config.json` and place the corresponding API key in `.env`.

Do not hard-code API keys in source files, upload them with project
submissions, or commit `.env` to a repository. The prototype should
retain its deterministic fallback behavior when no provider is
configured or an API request is unavailable.

## Human review

Treat all generated rankings, explanations, and creative briefs as
decision-support outputs. Before using or submitting them, review:

-   whether the cited creator and post evidence supports the
    recommendation;
-   whether the proposed content is appropriate for the creator and
    campaign;
-   advertising disclosure and platform requirements;
-   child-safety considerations where relevant;
-   factual accuracy and approved product-claim wording; and
-   any brand-safety or keyword flags.

The system assists marketing research and shortlisting; final creator
selection and campaign approval remain human decisions.
