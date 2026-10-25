# TapeLab: Class Diagrams

Three views of the same system: the database tables as Java entities, the Java backend classes built on them, and the Python objects that produce the data. Boxes marked `planned` do not exist yet.

## 1. Database entities (tables and how they relate)

```mermaid
classDiagram
    direction LR
    class Price {
        +PriceId id : ticker and date
        +BigDecimal open
        +BigDecimal high
        +BigDecimal low
        +BigDecimal close
        +long volume
    }
    class Filing {
        +Long id
        +String ticker
        +long cik
        +String form
        +String accession : unique
        +LocalDate filedAt
        +Instant acceptedAt
        +LocalDate periodEnd
        +String url
    }
    class FilingChunk {
        +Long id
        +int idx
        +ChunkKind kind : text or table
        +String text
    }
    class FilingScore {
        +FilingScoreId id : filing and model
        +double score : -1 to 1
        +String rationale
        +Instant scoredAt
    }
    class Decision {
        +Long id
        +String ticker
        +LocalDate decidedFor
        +Instant decidedAt
        +BigDecimal position : 0 to 1
        +List~Reason~ reasons : JSON
        +Map config : JSON
        <<insert-only>>
    }
    class Reason {
        +String analyst
        +double score
        +String rationale
    }
    class Order["Order (planned)"] {
        +Long id
        +String side
        +BigDecimal size
        +Instant filledAt
        +BigDecimal price
    }
    class BacktestRun["BacktestRun (planned)"] {
        +Long id
        +Map config
        +LocalDate windowStart
        +LocalDate windowEnd
        +int costBps
    }
    class BacktestMetric["BacktestMetric (planned)"] {
        +String name : sharpe, sortino, and so on
        +double value
    }
    Filing "1" --> "*" FilingChunk : has
    Filing "1" --> "*" FilingScore : scored by model
    Filing "0..1" --> "*" Decision : relied on
    Decision "1" *-- "*" Reason : explained by
    Decision "1" --> "0..1" Order : executed as
    BacktestRun "1" --> "*" BacktestMetric : produces
    Price .. Decision : same ticker and day (no foreign key)
```

## 2. Java backend (first endpoints, built on the entities)

```mermaid
classDiagram
    direction LR
    class PriceController {
        +list(ticker, from, to) List~PriceDto~
    }
    class DecisionController["DecisionController (planned)"] {
        +list(ticker, from, to) List~DecisionDto~
    }
    class PriceRepository {
        <<interface>>
        +findByIdTickerAndIdDateBetweenOrderByIdDate()
    }
    class DecisionRepository["DecisionRepository (planned)"] {
        <<interface>>
    }
    class PriceDto {
        <<record>>
        +LocalDate date
        +BigDecimal open
        +BigDecimal high
        +BigDecimal low
        +BigDecimal close
        +long volume
    }
    class DecisionDto["DecisionDto (planned)"] {
        <<record>>
    }
    class Price
    class Decision
    PriceController --> PriceRepository : reads
    PriceController ..> PriceDto : returns
    PriceRepository --> Price : manages
    DecisionController --> DecisionRepository : reads
    DecisionController ..> DecisionDto : returns
    DecisionRepository --> Decision : manages
```

## 3. Python engine (objects that produce the data)

```mermaid
classDiagram
    direction LR
    class PriceRow {
        <<dataclass, frozen>>
        +str ticker
        +date date
        +Decimal open
        +Decimal high
        +Decimal low
        +Decimal close
        +int volume
    }
    class FilingRef {
        <<dataclass, frozen>>
        +str ticker
        +int cik
        +str form
        +str accession
        +date filed_at
        +datetime accepted_at
        +date period_end
        +str url
    }
    class Chunk {
        <<dataclass, frozen>>
        +str text
        +str kind
        +str source
        +int index
    }
    class Signal {
        <<dataclass, frozen>>
        +str analyst
        +float score
        +str rationale
    }
    class Decision {
        <<dataclass, frozen>>
        +float position
        +tuple signals
    }
    class LLM {
        <<protocol>>
        +score_fundamentals(evidence) tuple
    }
    class GeminiLLM {
        +str model
        +RequestBudget budget
        +score_fundamentals(evidence)
    }
    class RuleBasedLLM {
        +score_fundamentals(evidence)
    }
    class RequestBudget {
        +int limit
        +int used
        +spend()
    }
    FilingRef --> Chunk : html_to_text then chunk_filing
    Chunk --> Signal : retrieved, then scored by LLM
    Signal "*" --> "1" Decision : blended by trader
    LLM <|.. GeminiLLM
    LLM <|.. RuleBasedLLM
    GeminiLLM --> RequestBudget : spends
    PriceRow ..> Signal : technical analyst reads closes
```

Note: the Python `Decision` is the trader's in-memory result (a position plus the signals behind it). It becomes a row of the database `Decision` entity when it is saved.
