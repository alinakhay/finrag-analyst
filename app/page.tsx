'use client';

import { useMemo, useState } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  Cpu,
  Database,
  Newspaper,
  Radio,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

type Catalyst = {
  id: string;
  category: string;
  direction: 'positive' | 'negative' | 'mixed';
  headline: string;
  source: string;
  time: string;
  confidence: number;
  quote: string;
  interpretation: string;
};

type Asset = {
  id: string;
  ticker: string;
  company: string;
  sector: string;
  price: number;
  move: number;
  benchmark: string;
  labels: string[];
  prices: number[];
  benchmarkPrices: number[];
  volumes: number[];
  eventIndex: number;
  car: number;
  volumeZ: number;
  volatility: number;
  beta: number;
  narrative: string;
  catalysts: Catalyst[];
};

const assets: Asset[] = [
  {
    id: 'astr',
    ticker: 'ASTR',
    company: 'Asteron Semiconductors',
    sector: 'Semiconductors',
    price: 184.62,
    move: 8.41,
    benchmark: 'SOX',
    labels: ['D-5', 'D-4', 'D-3', 'D-2', 'D-1', 'Event', 'D+1', 'D+2', 'D+3'],
    prices: [99.2, 99.8, 100.1, 99.7, 100.4, 105.9, 108.2, 108.8, 108.6],
    benchmarkPrices: [99.4, 99.7, 100.3, 100.0, 100.5, 101.2, 101.7, 102.0, 101.9],
    volumes: [17, 52, 23, 49, 22, 96, 78, 51, 43],
    eventIndex: 5,
    car: 6.5,
    volumeZ: 4.29,
    volatility: 405.1,
    beta: 1.18,
    narrative:
      'The move is most consistent with a guidance-led re-rating [astr-guidance]. Asteron also announced a multi-year accelerator supply agreement [astr-contract].',
    catalysts: [
      {
        id: 'astr-guidance',
        category: 'Guidance',
        direction: 'positive',
        headline: 'Management raises data-centre revenue outlook by 12%',
        source: 'Asteron investor update',
        time: '08:02 ET',
        confidence: 94,
        quote: 'We now expect data-centre revenue to grow 34–38% this fiscal year.',
        interpretation: 'A material upward revision to the segment carrying the highest valuation sensitivity.',
      },
      {
        id: 'astr-contract',
        category: 'Contract',
        direction: 'positive',
        headline: 'New accelerator supply agreement with a top-three cloud provider',
        source: 'MarketWire',
        time: '08:17 ET',
        confidence: 87,
        quote: 'Initial deployments begin next quarter under a multi-year capacity reservation.',
        interpretation: 'Adds demand visibility and supports the durability of the guidance revision.',
      },
    ],
  },
  {
    id: 'nvrb',
    ticker: 'NVRB',
    company: 'Novaridge Bank',
    sector: 'Regional banks',
    price: 41.08,
    move: -4.26,
    benchmark: 'KRE',
    labels: ['D-5', 'D-4', 'D-3', 'D-2', 'D-1', 'Event', 'D+1', 'D+2', 'D+3'],
    prices: [100.1, 100.4, 100.2, 99.8, 100.0, 96.8, 95.7, 95.9, 95.6],
    benchmarkPrices: [100.0, 100.1, 100.4, 100.0, 100.2, 99.7, 99.9, 100.1, 99.8],
    volumes: [15, 56, 22, 58, 34, 88, 72, 49, 45],
    eventIndex: 5,
    car: -4.06,
    volumeZ: 2.93,
    volatility: 354.4,
    beta: 0.91,
    narrative:
      'The sell-off appears credit-driven rather than a broad regional-bank move [nvrb-reserves]. A subsequent broker downgrade reduced earnings estimates and reinforced the move [nvrb-rating].',
    catalysts: [
      {
        id: 'nvrb-reserves',
        category: 'Credit',
        direction: 'negative',
        headline: 'Novaridge announces an unplanned commercial-real-estate reserve build',
        source: 'Novaridge press release',
        time: '07:31 ET',
        confidence: 96,
        quote: 'The quarter will include a $118 million provision tied primarily to office exposure.',
        interpretation: 'The magnitude was outside prior guidance and directly reduces near-term earnings.',
      },
      {
        id: 'nvrb-rating',
        category: 'Rating',
        direction: 'negative',
        headline: 'Broker cuts estimates following reserve announcement',
        source: 'North Coast Research',
        time: '09:06 ET',
        confidence: 78,
        quote: 'We reduce 2027 EPS by 9% and move the shares to Neutral.',
        interpretation: 'A secondary catalyst that reinforced the initial credit shock after the open.',
      },
    ],
  },
  {
    id: 'orbt',
    ticker: 'ORBT',
    company: 'Orbit Payments',
    sector: 'Financial technology',
    price: 76.34,
    move: 5.62,
    benchmark: 'FINX',
    labels: ['D-5', 'D-4', 'D-3', 'D-2', 'D-1', 'Event', 'D+1', 'D+2', 'D+3'],
    prices: [99.5, 99.9, 99.7, 100.3, 100.0, 103.7, 105.5, 105.8, 105.4],
    benchmarkPrices: [99.7, 99.8, 100.0, 100.2, 100.1, 100.8, 101.0, 101.3, 101.1],
    volumes: [24, 53, 29, 56, 43, 91, 70, 55, 49],
    eventIndex: 5,
    car: 4.08,
    volumeZ: 3.94,
    volatility: 307.5,
    beta: 1.07,
    narrative:
      'Orbit’s outperformance is linked to a regulatory clearance that removes a launch dependency [orbt-clearance]. Orbit subsequently confirmed a phased rollout to an initial merchant cohort [orbt-launch].',
    catalysts: [
      {
        id: 'orbt-clearance',
        category: 'Regulation',
        direction: 'positive',
        headline: 'Payments licence approved in two additional markets',
        source: 'Financial Conduct Authority bulletin',
        time: '06:45 ET',
        confidence: 95,
        quote: 'Orbit Payments is authorised to provide merchant acquiring services.',
        interpretation: 'Removes a key regulatory gate from the company’s international expansion plan.',
      },
      {
        id: 'orbt-launch',
        category: 'Product',
        direction: 'mixed',
        headline: 'Orbit confirms phased merchant rollout begins next month',
        source: 'Orbit company blog',
        time: '08:30 ET',
        confidence: 82,
        quote: 'The first cohort will include 1,200 small and mid-sized merchants.',
        interpretation: 'Supports revenue optionality, though the phased schedule limits near-term contribution.',
      },
    ],
  },
];

type MarketResult = {
  summary: string;
  metrics: {
    cumulative_abnormal_return: number;
    volume_z_score: number;
    volatility_change_pct: number;
    beta: number;
  };
  evidence: Catalyst[];
  trace: Array<{ name: string; detail: string; duration_ms: number }>;
  model_provider: string;
  citation_validation: {
    valid: boolean;
    cited_ids: string[];
    unsupported_ids: string[];
    uncited_claim_count: number;
    abstained: boolean;
    reason: string;
  };
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

function linePath(values: number[], width = 760, height = 260) {
  const min = Math.min(...values) - 1;
  const max = Math.max(...values) + 1;
  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / (max - min)) * height;
      return (index === 0 ? 'M' : 'L') + ' ' + x.toFixed(1) + ' ' + y.toFixed(1);
    })
    .join(' ');
}

export default function Home() {
  const [assetId, setAssetId] = useState('astr');
  const [question, setQuestion] = useState('What explains the unusual move in ASTR this week?');
  const [selectedCatalyst, setSelectedCatalyst] = useState('astr-guidance');
  const [view, setView] = useState<'brief' | 'evidence' | 'trace'>('brief');
  const [result, setResult] = useState<MarketResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const asset = useMemo(
    () => assets.find((item) => item.id === assetId) ?? assets[0],
    [assetId],
  );
  const evidence = result?.evidence ?? asset.catalysts;
  const metrics = result?.metrics ?? {
    cumulative_abnormal_return: asset.car,
    volume_z_score: asset.volumeZ,
    volatility_change_pct: asset.volatility,
    beta: asset.beta,
  };
  const trace = result?.trace ?? [
    { name: 'Fixture loading', detail: '2 validated synthetic records', duration_ms: 18 },
    { name: 'Catalyst retrieval', detail: 'lexical fixture baseline · 2 events', duration_ms: 24 },
    { name: 'Event study', detail: 'market-model window [-1, +3]', duration_ms: 11 },
    { name: 'Citation-ID guardrail', detail: 'fixture evidence IDs verified', duration_ms: 7 },
  ];

  function selectAsset(nextId: string) {
    const next = assets.find((item) => item.id === nextId) ?? assets[0];
    setAssetId(next.id);
    setSelectedCatalyst(next.catalysts[0].id);
    setQuestion('What explains the unusual move in ' + next.ticker + ' this week?');
    setResult(null);
    setError('');
  }

  async function runResearch() {
    if (!question.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      if (!apiBaseUrl) {
        await new Promise((resolve) => setTimeout(resolve, 450));
        setResult(null);
        return;
      }
      const response = await fetch(apiBaseUrl + '/api/v1/market-analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_id: asset.id,
          question,
          event_id: selectedCatalyst,
        }),
      });
      if (!response.ok) throw new Error('Research service returned ' + response.status);
      setResult(await response.json());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Research failed');
    } finally {
      setLoading(false);
    }
  }

  const selected = evidence.find((item) => item.id === selectedCatalyst) ?? evidence[0];
  const eventX = (asset.eventIndex / (asset.prices.length - 1)) * 760;

  return (
    <main className="market-app">
      <header className="market-header">
        <div className="market-brand">
          <span className="brand-signal"><Radio size={15} /></span>
          <div>
            <strong>CatalystLens</strong>
            <span>News-to-Market Impact Research</span>
          </div>
        </div>
        <div className="market-session">
          <span className="data-state"><i /> FIXTURE MODE</span>
          <span>EVENT WINDOW · 09 SEP 2026</span>
          <span className="model-pill"><Cpu size={13} /> EXTRACTIVE BASELINE</span>
        </div>
      </header>

      <div className="market-layout">
        <aside className="watch-panel">
          <div className="panel-heading">
            <span>Research universe</span>
            <Search size={14} />
          </div>
          <div className="asset-list">
            {assets.map((item) => (
              <button
                key={item.id}
                className={'asset-row ' + (item.id === asset.id ? 'active' : '')}
                onClick={() => selectAsset(item.id)}
              >
                <span>
                  <strong>{item.ticker}</strong>
                  <small>{item.sector}</small>
                </span>
                <span className={item.move >= 0 ? 'positive' : 'negative'}>
                  {item.move >= 0 ? '+' : ''}{item.move.toFixed(2)}%
                </span>
              </button>
            ))}
          </div>

          <div className="window-card">
            <span className="eyebrow">Study configuration</span>
            <dl>
              <div><dt>Estimation</dt><dd>120 trading days</dd></div>
              <div><dt>Event</dt><dd>[-1, +3]</dd></div>
              <div><dt>Model</dt><dd>Market beta</dd></div>
              <div><dt>Benchmark</dt><dd>{asset.benchmark}</dd></div>
            </dl>
          </div>

          <div className="pipeline-mini">
            <span className="eyebrow">Data pipeline</span>
            <p><CheckCircle2 size={14} /> Fixture news loaded</p>
            <p><CheckCircle2 size={14} /> Price bars aligned</p>
            <p><CheckCircle2 size={14} /> Citation IDs validated</p>
          </div>

          <p className="synthetic-disclosure">
            Demonstration data is synthetic and deterministic. No investment recommendation is produced.
          </p>
        </aside>

        <section className="market-workspace">
          <div className="asset-overview">
            <div>
              <span className="eyebrow">{asset.sector} · {asset.benchmark} benchmark</span>
              <h1>{asset.company} <span>{asset.ticker}</span></h1>
              <p>Event-driven research view</p>
            </div>
            <div className="price-lockup">
              <strong>USD {asset.price.toFixed(2)}</strong>
              <span className={asset.move >= 0 ? 'positive' : 'negative'}>
                {asset.move >= 0 ? <ArrowUpRight size={17} /> : <ArrowDownRight size={17} />}
                {asset.move >= 0 ? '+' : ''}{asset.move.toFixed(2)}%
              </span>
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-toolbar">
              <div>
                <span className="eyebrow">Indexed performance</span>
                <strong>Reaction around catalyst</strong>
              </div>
              <div className="legend">
                <span><i className="asset-line" /> {asset.ticker}</span>
                <span><i className="benchmark-line" /> {asset.benchmark}</span>
              </div>
            </div>
            <div className="price-chart">
              <svg viewBox="0 0 760 300" aria-labelledby="market-chart-title">
                <title id="market-chart-title">Indexed asset price versus benchmark</title>
                {[40, 100, 160, 220, 280].map((y) => (
                  <line key={y} className="chart-grid" x1="0" y1={y} x2="760" y2={y} />
                ))}
                <path className="benchmark-path" d={linePath(asset.benchmarkPrices)} />
                <path className="price-path" d={linePath(asset.prices)} />
                <line className="event-line" x1={eventX} y1="0" x2={eventX} y2="286" />
                <circle className="event-dot" cx={eventX} cy="91" r="5" />
                <text className="event-label" x={eventX + 9} y="18">CATALYST</text>
              </svg>
              <div className="chart-labels">
                {asset.labels.map((label) => <span key={label}>{label}</span>)}
              </div>
            </div>
            <div className="volume-bars" aria-label="Relative trading volume">
              {asset.volumes.map((volume, index) => (
                <i
                  key={asset.labels[index]}
                  className={index === asset.eventIndex ? 'event-volume' : ''}
                  style={{ height: volume + '%' }}
                />
              ))}
            </div>
          </div>

          <section className="catalyst-section">
            <div className="section-title">
              <div><Newspaper size={16} /><strong>Detected catalysts</strong></div>
              <span>{asset.catalysts.length} material events</span>
            </div>
            <div className="catalyst-grid">
              {asset.catalysts.map((catalyst) => (
                <button
                  key={catalyst.id}
                  onClick={() => setSelectedCatalyst(catalyst.id)}
                  className={'catalyst-card ' + catalyst.direction + ' ' + (selectedCatalyst === catalyst.id ? 'selected' : '')}
                >
                  <div className="catalyst-meta">
                    <span>{catalyst.category}</span>
                    <span>{catalyst.time}</span>
                  </div>
                  <strong>{catalyst.headline}</strong>
                  <p>{catalyst.interpretation}</p>
                  <small>{catalyst.source} · {catalyst.confidence}% fixture relevance score</small>
                </button>
              ))}
            </div>
          </section>

          <section className="research-card">
            <div className="research-input">
              <Sparkles size={17} />
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => { if (event.key === 'Enter') void runResearch(); }}
                aria-label="Research question"
              />
              <Button onClick={() => void runResearch()} disabled={loading}>
                {loading ? 'Running…' : 'Run research'}
              </Button>
            </div>
            {error ? <p className="analysis-error">{error}</p> : null}
            <div className="research-tabs">
              {(['brief', 'evidence', 'trace'] as const).map((tab) => (
                <button key={tab} className={view === tab ? 'active' : ''} onClick={() => setView(tab)}>
                  {tab}
                </button>
              ))}
            </div>

            {view === 'brief' ? (
              <div className="impact-brief">
                <div className="brief-confidence">
                  <ShieldCheck size={17} />
                  <span>
                    <strong>{result?.citation_validation.abstained ? 'Safely abstained' : 'Evidence checked'}</strong>
                    {' · '}{result?.citation_validation.reason ?? 'deterministic fixture with explicit evidence IDs'}
                  </span>
                </div>
                <h2>Market impact brief</h2>
                <p>{result?.summary ?? asset.narrative}</p>
                <div className="selected-source">
                  <span>Primary catalyst</span>
                  <strong>{selected.headline}</strong>
                  <blockquote>“{selected.quote}”</blockquote>
                </div>
              </div>
            ) : null}

            {view === 'evidence' ? (
              <div className="evidence-list">
                {evidence.map((item, index) => (
                  <article key={item.id}>
                    <span>0{index + 1}</span>
                    <div>
                      <small>{item.source} · {item.time}</small>
                      <strong>{item.headline}</strong>
                      <blockquote>“{item.quote}”</blockquote>
                    </div>
                  </article>
                ))}
              </div>
            ) : null}

            {view === 'trace' ? (
              <div className="trace-list">
                {trace.map((step, index) => (
                  <article key={step.name}>
                    <span>0{index + 1}</span>
                    <div><strong>{step.name}</strong><small>{step.detail}</small></div>
                    <time>{step.duration_ms} ms</time>
                  </article>
                ))}
              </div>
            ) : null}
          </section>
        </section>

        <aside className="study-panel">
          <div className="panel-heading">
            <span>Event study</span>
            <BarChart3 size={15} />
          </div>
          <div className={'metric-hero ' + (metrics.cumulative_abnormal_return >= 0 ? 'positive' : 'negative')}>
            <span>5-day CAR</span>
            <strong>{metrics.cumulative_abnormal_return >= 0 ? '+' : ''}{metrics.cumulative_abnormal_return.toFixed(2)}%</strong>
            <small>vs {asset.benchmark}, beta-adjusted</small>
          </div>
          <div className="metric-grid">
            <article>
              <span>Volume shock</span>
              <strong>{metrics.volume_z_score.toFixed(1)}σ</strong>
              <Progress value={Math.min(metrics.volume_z_score * 18, 100)} />
            </article>
            <article>
              <span>Volatility change</span>
              <strong>+{metrics.volatility_change_pct.toFixed(0)}%</strong>
              <Progress value={Math.min(metrics.volatility_change_pct, 100)} />
            </article>
            <article>
              <span>Estimated beta</span>
              <strong>{metrics.beta.toFixed(2)}</strong>
              <Progress value={Math.min(metrics.beta * 60, 100)} />
            </article>
          </div>

          <div className="attribution-card">
            <span className="eyebrow">Illustrative fixture attribution</span>
            {asset.catalysts.map((item, index) => (
              <div key={item.id}>
                <span>{item.category}</span>
                <strong>{index === 0 ? '68%' : '24%'}</strong>
              </div>
            ))}
            <div><span>Unexplained</span><strong>8%</strong></div>
          </div>

          <div className="model-card">
            <div><Database size={17} /><span>Inference</span></div>
            <strong>Deterministic extractor</strong>
            <p>Optional local PEFT/LoRA path</p>
            <span className="model-status"><i /> {result?.model_provider ?? 'extractive-fixture'}</span>
          </div>

          <div className="method-note">
            <Activity size={16} />
            <p><strong>Research, not prediction.</strong> CatalystLens measures observed market reaction and preserves source provenance.</p>
          </div>
        </aside>
      </div>
    </main>
  );
}
