'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowUpRight,
  Check,
  CircleAlert,
  FileText,
  Loader2,
  Search,
  Send,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

type Filing = {
  id: string;
  company: string;
  meta: string;
  sector: string;
  score: number;
  level: string;
  delta: string;
  exposure: Array<{ label: string; value: number }>;
  questions: string[];
  answer: string;
  points: string[];
  sources: Array<{
    section: string;
    page: string;
    score: string;
    quote: string;
  }>;
};

const filings: Filing[] = [
  {
    id: 'meridian',
    company: 'Meridian National Bank',
    meta: 'FY 2025 · Form 10-K',
    sector: 'Banking',
    score: 72,
    level: 'Elevated',
    delta: '+8 pts YoY',
    exposure: [
      { label: 'Credit', value: 78 },
      { label: 'Liquidity', value: 61 },
      { label: 'Market', value: 48 },
      { label: 'Operational', value: 69 },
    ],
    questions: [
      'What changed in credit risk?',
      'Summarise liquidity pressure',
      'Where is management most cautious?',
    ],
    answer:
      'Credit risk increased materially in 2025, led by commercial real-estate concentration and weaker debt-service coverage among mid-market borrowers.',
    points: [
      'Non-performing CRE loans rose from 1.8% to 2.6% of the portfolio.',
      'Office exposure is concentrated in three metropolitan markets with slower leasing activity.',
      'The allowance for credit losses increased 14%, outpacing loan growth of 4%.',
    ],
    sources: [
      {
        section: 'Item 7 · Credit Risk',
        page: 'p. 84',
        score: '0.94',
        quote:
          'Commercial real estate non-performing loans increased to 2.6% from 1.8%, primarily within the office portfolio.',
      },
      {
        section: 'Item 1A · Risk Factors',
        page: 'p. 31',
        score: '0.89',
        quote:
          'Refinancing pressure may intensify where collateral values and occupancy remain below pre-2023 levels.',
      },
    ],
  },
  {
    id: 'northstar',
    company: 'Northstar Asset Management',
    meta: 'FY 2025 · Form 10-K',
    sector: 'Asset management',
    score: 54,
    level: 'Moderate',
    delta: '-3 pts YoY',
    exposure: [
      { label: 'Credit', value: 42 },
      { label: 'Liquidity', value: 58 },
      { label: 'Market', value: 67 },
      { label: 'Operational', value: 49 },
    ],
    questions: [
      'What could pressure fee revenue?',
      'Summarise redemption risk',
      'How exposed is the firm to rates?',
    ],
    answer:
      'The main earnings sensitivity is market-led: lower asset values and net outflows would reduce management fees, while performance fees remain concentrated in two strategies.',
    points: [
      'Assets under management grew 6%, but active equity strategies recorded net outflows.',
      'Two alternative strategies generated 63% of performance fees.',
      'Liquidity buffers cover modeled redemptions under the severe internal scenario.',
    ],
    sources: [
      {
        section: 'Item 7 · AUM and flows',
        page: 'p. 67',
        score: '0.92',
        quote:
          'Net outflows in active equities partially offset market appreciation across the broader platform.',
      },
      {
        section: 'Item 1A · Market risk',
        page: 'p. 28',
        score: '0.86',
        quote:
          'Performance fee revenue remains dependent on a limited number of alternative investment strategies.',
      },
    ],
  },
  {
    id: 'helix',
    company: 'Helix Payments Group',
    meta: 'FY 2025 · Form 10-K',
    sector: 'Payments',
    score: 64,
    level: 'Heightened',
    delta: '+5 pts YoY',
    exposure: [
      { label: 'Credit', value: 31 },
      { label: 'Liquidity', value: 39 },
      { label: 'Market', value: 44 },
      { label: 'Operational', value: 83 },
    ],
    questions: [
      'What is the largest operational risk?',
      'Summarise regulatory exposure',
      'Explain the fraud-loss trend',
    ],
    answer:
      'Operational risk is the dominant concern, driven by rising account-takeover fraud, reliance on two processing partners, and expanding regulatory obligations across new markets.',
    points: [
      'Fraud losses increased 21% as transaction volume grew 13%.',
      'Two external processors handle most authorization traffic.',
      'Management accelerated investment in identity controls and incident response.',
    ],
    sources: [
      {
        section: 'Item 7 · Transaction losses',
        page: 'p. 73',
        score: '0.96',
        quote:
          'Transaction losses increased 21%, primarily reflecting account-takeover activity and higher cross-border volume.',
      },
      {
        section: 'Item 1A · Operations',
        page: 'p. 24',
        score: '0.91',
        quote:
          'A significant interruption at either primary processing partner could delay transaction authorization.',
      },
    ],
  },
];

type ApiResult = {
  answer: string;
  bullets: string[];
  citations: Array<{
    section: string;
    page: number;
    score: number;
    quote: string;
  }>;
  groundedness: number;
  risk_score: number;
  risk_level: string;
  exposure: Array<{ category: string; score: number }>;
  trace: Array<{ name: string; detail: string; duration_ms: number }>;
  model_provider: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export default function Home() {
  const [filingId, setFilingId] = useState('meridian');
  const [question, setQuestion] = useState('What changed in credit risk?');
  const [submittedQuestion, setSubmittedQuestion] = useState(question);
  const [isLoading, setIsLoading] = useState(false);
  const [runCount, setRunCount] = useState(24);
  const [apiResult, setApiResult] = useState<ApiResult | null>(null);
  const [error, setError] = useState('');
  const [view, setView] = useState<'memo' | 'trace'>('memo');
  const filing = useMemo(
    () => filings.find((item) => item.id === filingId) ?? filings[0],
    [filingId],
  );
  const presentation = {
    answer: apiResult?.answer ?? filing.answer,
    bullets: apiResult?.bullets ?? filing.points,
    sources: apiResult?.citations ?? filing.sources,
    riskScore: apiResult?.risk_score ?? filing.score,
    riskLevel: apiResult?.risk_level ?? filing.level,
    exposure:
      apiResult?.exposure.map((item) => ({
        label: item.category[0].toUpperCase() + item.category.slice(1),
        value: item.score,
      })) ?? filing.exposure,
    groundedness: apiResult ? Math.round(apiResult.groundedness * 100) : 93,
    modelProvider: apiResult?.model_provider ?? 'huggingface-lora',
    trace: apiResult?.trace.map((step) => [
      step.name,
      step.detail,
      `${step.duration_ms} ms`,
    ]) ?? [
      ['Query expansion', 'finance risk ontology', '8 ms'],
      ['Evidence retrieval', 'BM25 + dense vectors', '21 ms'],
      ['Grounded generation', 'local LoRA adapter', '684 ms'],
      ['Citation guardrail', '2 claims linked', '4 ms'],
    ],
  };
  const confidence =
    presentation.groundedness >= 90
      ? 'High'
      : presentation.groundedness >= 75
        ? 'Moderate'
        : 'Review';

  function changeFiling(value: string | null) {
    const nextValue = value ?? 'meridian';
    const next = filings.find((item) => item.id === nextValue) ?? filings[0];
    setFilingId(nextValue);
    setQuestion(next.questions[0]);
    setSubmittedQuestion(next.questions[0]);
    setApiResult(null);
    setError('');
  }

  const runAnalysis = useCallback(
    async (nextQuestion = question, targetFilingId = filingId) => {
      if (!nextQuestion.trim() || isLoading) return null;
      setIsLoading(true);
      setError('');
      try {
        let result: ApiResult | null = null;
        if (apiBaseUrl) {
          const response = await fetch(`${apiBaseUrl}/api/v1/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              filing_id: targetFilingId,
              question: nextQuestion.trim(),
            }),
          });
          if (!response.ok)
            throw new Error(`Analysis failed (${response.status})`);
          result = (await response.json()) as ApiResult;
          setApiResult(result);
        } else {
          await new Promise((resolve) => window.setTimeout(resolve, 550));
        }
        setFilingId(targetFilingId);
        setQuestion(nextQuestion.trim());
        setSubmittedQuestion(nextQuestion.trim());
        setRunCount((count) => count + 1);
        return result;
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'Analysis failed');
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [filingId, isLoading, question],
  );

  useEffect(() => {
    type WebMcpContext = {
      registerTool: (
        tool: Record<string, unknown>,
        options?: { signal?: AbortSignal },
      ) => void | Promise<void>;
    };
    const context = (document as Document & { modelContext?: WebMcpContext })
      .modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    const registration = context.registerTool(
      {
        name: 'analyze_financial_filing',
        title: 'Analyze financial filing',
        description:
          'Ask an evidence-grounded risk question about one of the indexed demo filings and update the visible analysis.',
        inputSchema: {
          type: 'object',
          properties: {
            filingId: { type: 'string', enum: filings.map((item) => item.id) },
            question: { type: 'string', minLength: 5, maxLength: 500 },
          },
          required: ['filingId', 'question'],
          additionalProperties: false,
        },
        annotations: { readOnlyHint: true, untrustedContentHint: false },
        execute: async (input: unknown) => {
          if (!input || typeof input !== 'object')
            throw new Error('Input must be an object.');
          const value = input as { filingId?: unknown; question?: unknown };
          if (
            typeof value.filingId !== 'string' ||
            !filings.some((item) => item.id === value.filingId)
          )
            throw new Error('Unknown filingId.');
          if (
            typeof value.question !== 'string' ||
            value.question.trim().length < 5
          )
            throw new Error('Question must contain at least 5 characters.');
          const result = await runAnalysis(value.question, value.filingId);
          return {
            filingId: value.filingId,
            question: value.question,
            groundedness: result?.groundedness ?? 0.93,
            sourceCount: result?.citations.length ?? 2,
          };
        },
      },
      { signal: lifecycle.signal },
    );
    void Promise.resolve(registration).catch(() => undefined);
    return () => lifecycle.abort();
  }, [runAnalysis]);

  return (
    <main className="application-frame">
      <header className="masthead">
        <a className="wordmark" href="#top" aria-label="FinRAG Analyst home">
          <span className="wordmark-index">FR</span>
          <span>FinRAG Analyst</span>
        </a>
        <p className="masthead-desk">
          Financial risk intelligence / research environment
        </p>
        <div className="connection-state">
          <span className="connection-light" />
          {apiBaseUrl ? 'Local engine connected' : 'Showcase dataset'}
        </div>
      </header>

      <div className="workspace" id="top">
        <aside className="scope-rail">
          <div className="rail-section">
            <span className="rail-number">01</span>
            <p className="micro-label">Document scope</p>
            <Select value={filingId} onValueChange={changeFiling}>
              <SelectTrigger
                className="filing-select"
                aria-label="Select a filing"
              >
                <SelectValue>{filing.company}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                {filings.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.company}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="filing-meta">
              {filing.meta}
              <br />
              {filing.sector}
            </p>
          </div>

          <div className="rail-section score-section">
            <span className="rail-number">02</span>
            <p className="micro-label">Risk assessment</p>
            <div className="score-lockup">
              <span className="score-value">{presentation.riskScore}</span>
              <span className="score-denominator">/100</span>
            </div>
            <strong className="score-level">{presentation.riskLevel}</strong>
            <span className="score-delta">{filing.delta}</span>
          </div>

          <div className="rail-section exposure-section">
            <div className="section-line">
              <span>Exposure</span>
              <span>Score</span>
            </div>
            {presentation.exposure.map((item) => (
              <div className="exposure-row" key={item.label}>
                <div>
                  <span>{item.label}</span>
                  <b>{item.value}</b>
                </div>
                <Progress
                  value={item.value}
                  aria-label={`${item.label} risk ${item.value}`}
                />
              </div>
            ))}
          </div>
          <div className="document-footnote">
            <FileText size={17} />
            <p>
              <strong>Indexed locally</strong>
              <span>186 chunks / 42,318 tokens</span>
            </p>
            <Check size={15} />
          </div>
          <p className="synthetic-note">
            <CircleAlert size={14} /> Synthetic demonstration data
          </p>
        </aside>

        <section className="memo-sheet">
          <div className="memo-heading">
            <div>
              <p className="issue-line">Risk memorandum / Issue 01</p>
              <h1>{filing.company}</h1>
              <p className="memo-deck">
                Evidence-grounded review of material risk disclosures
              </p>
            </div>
            <div className="model-stamp">
              <span>MODEL</span>
              <strong>
                {presentation.modelProvider.includes('lora')
                  ? 'FIN-QA / LORA'
                  : 'QWEN / BASE'}
              </strong>
              <small>
                {presentation.modelProvider.replace('huggingface-', '')} · local
              </small>
            </div>
          </div>

          <div className="question-composer">
            <Search size={19} aria-hidden="true" />
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if ((event.metaKey || event.ctrlKey) && event.key === 'Enter')
                  void runAnalysis();
              }}
              aria-label="Ask a question about the filing"
              placeholder="Ask a material-risk question…"
              className="question-input"
            />
            <Button
              onClick={() => void runAnalysis()}
              disabled={isLoading || !question.trim()}
              className="analyze-button"
            >
              {isLoading ? (
                <Loader2 className="animate-spin" size={17} />
              ) : (
                <Send size={16} />
              )}
              Run analysis
            </Button>
          </div>
          <div className="suggested-queries">
            <span>Suggested</span>
            {filing.questions.map((item, index) => (
              <button key={item} onClick={() => setQuestion(item)}>
                {String(index + 1).padStart(2, '0')} — {item}
              </button>
            ))}
          </div>
          {error ? (
            <p className="analysis-error" role="alert">
              {error}. The showcase response remains visible.
            </p>
          ) : null}

          <div className="memo-tabs" role="tablist" aria-label="Analysis view">
            <button
              role="tab"
              aria-selected={view === 'memo'}
              className={view === 'memo' ? 'active' : ''}
              onClick={() => setView('memo')}
            >
              Analyst memo
            </button>
            <button
              role="tab"
              aria-selected={view === 'trace'}
              className={view === 'trace' ? 'active' : ''}
              onClick={() => setView('trace')}
            >
              Retrieval trace
            </button>
            <span>RUN-{String(runCount).padStart(4, '0')}</span>
          </div>

          {view === 'memo' ? (
            <div className={`memo-body ${isLoading ? 'answer-loading' : ''}`}>
              <p className="answered-question">
                Question / {submittedQuestion}
              </p>
              <p className="answer-lede">{presentation.answer}</p>
              <ol className="finding-list">
                {presentation.bullets.map((point, index) => (
                  <li key={point}>
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    <p>{point}</p>
                  </li>
                ))}
              </ol>
              <div className="assurance-strip">
                <span className="assurance-mark">
                  <Check size={15} />
                </span>
                <p>
                  <strong>{confidence} evidence coverage</strong>
                  <span>
                    {presentation.sources.length} independent passages retrieved
                  </span>
                </p>
                <b>{presentation.groundedness}%</b>
              </div>
              <section className="evidence-section">
                <div className="section-line">
                  <span>Evidence register</span>
                  <span>{presentation.sources.length} passages</span>
                </div>
                {presentation.sources.map((source, index) => (
                  <article
                    className="evidence-row"
                    key={`${source.section}-${index}`}
                  >
                    <span className="evidence-index">[{index + 1}]</span>
                    <div>
                      <h2>{source.section}</h2>
                      <blockquote>“{source.quote}”</blockquote>
                    </div>
                    <div className="evidence-meta">
                      <span>
                        {typeof source.page === 'number'
                          ? `p. ${source.page}`
                          : source.page}
                      </span>
                      <span>{source.score} match</span>
                    </div>
                  </article>
                ))}
              </section>
            </div>
          ) : (
            <div className="trace-table" role="tabpanel">
              {presentation.trace.map(([label, detail, timing], index) => (
                <div className="trace-row" key={label}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <strong>{label}</strong>
                  <p>{detail}</p>
                  <code>{timing}</code>
                </div>
              ))}
            </div>
          )}
        </section>

        <aside className="audit-rail">
          <div className="audit-heading">
            <p className="micro-label">Model assurance</p>
            <span className="live-marker">Live</span>
          </div>
          <div className="groundedness">
            <span>
              {presentation.groundedness}
              <small>%</small>
            </span>
            <p>Groundedness</p>
            <div aria-hidden="true">
              <i style={{ width: `${presentation.groundedness}%` }} />
            </div>
          </div>
          <dl className="quality-grid">
            <div>
              <dt>Faithfulness</dt>
              <dd>0.91</dd>
            </div>
            <div>
              <dt>Context recall</dt>
              <dd>0.88</dd>
            </div>
          </dl>
          <div className="pipeline-section">
            <div className="section-line">
              <span>Inference route</span>
              <span>4 stages</span>
            </div>
            {[
              ['01', 'Retrieve', 'BM25 + Qdrant'],
              ['02', 'Rerank', 'cross-encoder'],
              ['03', 'Generate', presentation.modelProvider],
              ['04', 'Verify', 'citation guard'],
            ].map(([number, label, detail]) => (
              <div className="pipeline-row" key={number}>
                <span>{number}</span>
                <p>
                  <strong>{label}</strong>
                  <small>{detail}</small>
                </p>
                <Check size={14} />
              </div>
            ))}
          </div>
          <div className="runtime-section">
            <div className="section-line">
              <span>Runtime</span>
              <span>Local</span>
            </div>
            <dl>
              <div>
                <dt>p95 latency</dt>
                <dd>812 ms</dd>
              </div>
              <div>
                <dt>Requests</dt>
                <dd>1,284</dd>
              </div>
              <div>
                <dt>Error rate</dt>
                <dd>0.08%</dd>
              </div>
            </dl>
          </div>
          <a
            className="architecture-link"
            href="https://github.com/alinakhay/finrag-analyst"
            target="_blank"
            rel="noreferrer"
          >
            View architecture <ArrowUpRight size={15} />
          </a>
          <p className="stack-signature">
            FastAPI / Qdrant / PEFT
            <br />
            Prometheus / Docker Compose
          </p>
        </aside>
      </div>
    </main>
  );
}
