import React from "react";
import { createRoot } from "react-dom/client";
import {
  ActionIcon,
  Alert,
  AppShell,
  Badge,
  Button,
  Checkbox,
  Collapse,
  Group,
  Loader,
  MantineProvider,
  Menu,
  Modal,
  Paper,
  Popover,
  PasswordInput,
  ScrollArea,
  SegmentedControl,
  Select,
  Skeleton,
  Stack,
  Table,
  Tabs,
  Text,
  TextInput,
  Textarea,
  ThemeIcon,
  Tooltip,
  UnstyledButton
} from "@mantine/core";
import { Notifications, notifications } from "@mantine/notifications";
import { DateInput, DatesProvider } from "@mantine/dates";
import "dayjs/locale/zh-cn";
import {
  IconContext,
  ActivityIcon as Activity,
  WarningIcon as AlertTriangle,
  ChartBarIcon as BarChart3,
  RobotIcon as Bot,
  BookOpenIcon as BookOpen,
  BrainIcon as BrainCircuit,
  CalendarDotsIcon as CalendarDays,
  ChartLineIcon as ChartCandlestick,
  CheckIcon as Check,
  CaretDownIcon as ChevronDown,
  CaretLeftIcon as ChevronLeft,
  CaretRightIcon as ChevronRight,
  ClipboardTextIcon as ClipboardList,
  DatabaseIcon as Database,
  ArrowSquareOutIcon as ExternalLink,
  InfoIcon as Info,
  ListChecksIcon as ListChecks,
  MegaphoneIcon as Megaphone,
  PauseIcon as Pause,
  PencilSimpleIcon as Pencil,
  PlayIcon as Play,
  ArrowsClockwiseIcon as RefreshCw,
  ReceiptIcon as Receipt,
  MagnifyingGlassIcon as Search,
  PaperPlaneTiltIcon as Send,
  ShieldWarningIcon as ShieldAlert,
  ShieldCheckIcon as ShieldCheck,
  StarIcon as Star,
  TrendDownIcon as TrendingDown,
  TrendUpIcon as TrendingUp,
  XCircleIcon as XCircle,
  UserGearIcon as UserCog,
  SlidersHorizontalIcon as SlidersHorizontal,
  WalletIcon as WalletCards
} from "@phosphor-icons/react";
import {
  CandlestickData,
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  HistogramData,
  HistogramSeries,
  IChartApi,
  ISeriesApi,
  ISeriesMarkersPluginApi,
  LineData,
  LineSeries,
  LogicalRange,
  SeriesMarker,
  Time
} from "lightweight-charts";
import { mantineTheme } from "./mantineTheme";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import "@mantine/dates/styles.css";
import "./styles.css";

type PrimarySection = "market" | "trade" | "orders" | "automation" | "account" | "settings";
type MarketTab = "radar" | "chart" | "aiOutlook" | "aiRecords" | "stats" | "announcements" | "usTimeline" | "overview";
type AutomationTab = "overview" | "strategies" | "signals" | "signalDetail";
type AccountTab = "positions" | "account" | "earn";
type SettingsTab = "llm" | "usage";

type AppRouteState = {
  section: PrimarySection;
  marketTab: MarketTab;
  automationTab: AutomationTab;
  accountTab: AccountTab;
  settingsTab: SettingsTab;
  signalDetailId: number | null;
  selectedContract: string;
  selectedBar: string;
  timelineDate: string;
};

type UsMarketEvent = { id: string; title: string; category: string; importance: string; state: string; scheduledAt?: number | null; timeKnown?: boolean; sourceTimezone?: string; actual?: string | null; forecast?: string | null; previousValue?: string | null; revision?: string | null; unit?: string | null; period_label?: string | null; sourceUrl: string; sourceSummary?: string; provider: string; };
type UsMarketProviderStatus = { provider: string; status: "fresh" | "retained" | "unavailable"; eventCount?: number; retainedCount?: number; message?: string; };
type UsMarketEventsResponse = { data: UsMarketEvent[]; warnings?: string[]; providers?: string[]; providerStatuses?: UsMarketProviderStatus[]; cacheAgeMs?: number; refreshing?: boolean; };
type PlatformVolumeResponse = { data: { volUsd: string; ts: number } | null; state: "fresh" | "cached" | "loading" | "unavailable"; message: string; source: string; cacheAgeMs?: number | null; ts?: number | null; };
type VolumeHistoryPoint = { date: string; ts: number; volUsd: string; count: number; confirm: string };
type VolumePeriod = "day" | "week" | "month" | "year";
type VolumeHistoryResponse = {
  data: {
    daily: VolumeHistoryPoint[];
    instrumentCount: number;
    requestedCount: number;
    universeCount: number;
    coveragePct: number;
    startDate: string;
    endDate: string;
    quoteCurrency: string;
    source: string;
  } | null;
  state: "fresh" | "cached" | "loading" | "unavailable";
  message: string;
  source: string;
  cacheAgeMs?: number | null;
  ts?: number | null;
};

type Instrument = {
  inst_id: string;
  inst_type: string;
  inst_family?: string;
  settle_ccy?: string;
  ct_val?: string;
  ct_val_ccy?: string;
  tick_sz?: string;
  lot_sz?: string;
  state?: string;
  watched?: number;
};

type Candle = {
  ts: number | string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  volumeCcy?: string;
  volumeQuote?: string;
  confirm?: string;
};

type CandleDetailSnapshot = {
  instId: string;
  bar: string;
  candle: Candle;
  previous: Candle | null;
  averages: MovingAverageValues | null;
  source: string;
};

type ChartSnapshotMetadata = {
  snapshotId: string;
  instId: string;
  bar: string;
  candleCount: number;
  lastCandleTs: number;
  snapshotTs: number;
  source: string;
  warning?: string;
  complete: boolean;
  currentCandleOpen: boolean;
};

type AccountResponse = {
  configured: boolean;
  environment?: "simulated" | "live";
  summary: null | Record<string, unknown>;
  positions: Array<Record<string, string>>;
  message?: string;
  source?: string;
  ts?: number;
  cacheAgeMs?: number;
  warning?: string;
  refresh?: {
    state: "not_configured" | "initializing" | "unavailable" | "refreshing" | "backing_off" | "fresh" | "stale";
    label: string;
    snapshotTs?: number | null;
    cacheAgeMs?: number | null;
    nextRetryAt?: number | null;
    failureCount?: number;
  };
};

type EarnDataItem = {
  ccy?: string;
  bal?: string;
  amt?: string;
  minAmt?: string;
  maxAmt?: string;
  earnings?: string;
  realizedEarnings?: string;
  redeemingAmt?: string;
  earningType?: string;
  earningTypeLabel?: string;
};

type EarnProduct = {
  productId: string;
  ccy: string;
  protocol: string;
  protocolType: string;
  term: string;
  apy: string;
  earlyRedeem?: boolean;
  state: string;
  stateLabel: string;
  investData: EarnDataItem[];
  earningData: EarnDataItem[];
  redeemPeriod: string[];
  fastRedemptionDailyLimit: string;
};

type EarnOrder = {
  ordId: string;
  ccy: string;
  productId: string;
  state: string;
  stateLabel: string;
  protocol: string;
  protocolType: string;
  term: string;
  apy: string;
  investData: EarnDataItem[];
  earningData: EarnDataItem[];
  fastRedemptionData?: EarnDataItem[];
  purchasedTime?: string;
  redeemedTime?: string;
  estSettlementTime?: string;
  cancelRedemptionDeadline?: string;
  tag?: string;
};

type EarnListResponse<T> = {
  configured?: boolean;
  environment?: "simulated" | "live";
  section?: string;
  data: T[];
  paging?: {
    limit?: number;
    hasMore?: boolean;
    after?: string;
    before?: string;
  };
  message?: string;
  source?: string;
  ts?: number;
  cacheAgeMs?: number;
  warnings?: string[];
};

type EarnStakingProductInfo = {
  asset?: string;
  receiptCcy?: string;
  rate?: string;
  redemptDays?: string;
  minAmt?: string;
  fastRedemptionDailyLimit?: string;
  fastRedemptionAvail?: string;
};

type EarnStakingBalance = {
  asset?: string;
  ccy?: string;
  amt?: string;
  latestInterestAccrual?: string;
  totalInterestAccrual?: string;
  ts?: string;
};

type EarnStakingHistory = {
  type?: string;
  amt?: string;
  redeemingAmt?: string;
  status?: string;
  statusLabel?: string;
  ordId?: string;
  requestTime?: string;
  completedTime?: string;
  estCompletedTime?: string;
};

type EarnApyPoint = {
  ts: number;
  rate: string;
};

type EarnStakingResponse = {
  configured?: boolean;
  environment?: "simulated" | "live";
  asset: "ETH" | "SOL";
  receiptCcy: "BETH" | "OKSOL";
  productInfo?: EarnStakingProductInfo;
  balances: EarnStakingBalance[];
  history: EarnStakingHistory[];
  apyPoints: EarnApyPoint[];
  paging?: {
    limit?: number;
    hasMore?: boolean;
    after?: string;
    before?: string;
  };
  days?: number;
  source?: string;
  ts?: number;
  cacheAgeMs?: number;
  warnings?: string[];
};

type Ticker = Record<string, string>;
type TickerRefresh = {
  state?: "fresh" | "refreshing" | "backing_off" | "stale" | "initializing" | "unavailable" | string;
  label?: string;
  snapshotTs?: number | null;
  cacheAgeMs?: number | null;
  nextRetryAt?: number | null;
  failureCount?: number;
};
type TickersResponse = {
  data?: Ticker[];
  source?: string;
  ts?: number;
  warning?: string;
  refresh?: TickerRefresh;
};

type MarketLongShortStats = {
  latest?: string;
  latestTs?: number;
  bias?: string;
  points?: Array<{ ts: number; ratio?: string }>;
};

type MarketTakerVolumeStats = {
  latestTs?: number;
  sellVol?: string;
  buyVol?: string;
  totalVol?: string;
  buySharePct?: string;
  buySellRatio?: string;
  dominance?: string;
  unit?: string;
  points?: Array<{
    ts: number;
    sellVol?: string;
    buyVol?: string;
    totalVol?: string;
    buySharePct?: string;
    buySellRatio?: string;
  }>;
};

type MarketOpenInterestStats = {
  latestTs?: number;
  oi?: string;
  oiCcy?: string;
  oiUsd?: string;
  change?: string;
  changePct?: string;
  trend?: string;
  points?: Array<{ ts: number; oi?: string; oiCcy?: string; oiUsd?: string }>;
};

type MarketStatsResponse = {
  instId: string;
  requestedPeriod?: string;
  period?: string;
  limit?: number;
  source?: string;
  ts?: number;
  cacheAgeMs?: number | null;
  warnings?: string[];
  longShortAccountRatio?: MarketLongShortStats;
  takerVolume?: MarketTakerVolumeStats;
  openInterest?: MarketOpenInterestStats;
};

type MarketAiSource = {
  source?: string;
  title?: string;
  url?: string;
  publishedAt?: string;
  scheduledAt?: string;
  cacheAgeMs?: number | null;
  official?: boolean;
};

type MarketAiPriceLogic = {
  direction?: string;
  entry?: string;
  stop?: string;
  target?: string;
  validity?: string;
};

type MarketAiOutlookResponse = {
  status?: "ok" | "fallback" | string;
  source?: string;
  provider?: string;
  model?: string;
  promptVersion?: string;
  analysisProfile?: {
    id?: string;
    profileVersion?: number;
    contentHash?: string;
    dataPolicy?: string;
    status?: "active" | "invalid" | string;
    upstream?: {
      repository?: string;
      path?: string;
      version?: string;
      commit?: string;
      license?: string;
    };
  };
  generatedAt?: number;
  stance?: "bullish" | "bearish" | "neutral" | "wait" | string;
  confidence?: number;
  summary?: string;
  overall?: {
    view?: string;
    confidence?: number;
    summary?: string;
  };
  horizons?: Array<{
    key?: "15m" | "1h" | "today" | string;
    label?: string;
    bias?: string;
    confidence?: number;
    summary?: string;
    watch?: string[];
    risk?: string;
  }>;
  report?: {
    keyFactors?: string[];
    focus?: string[];
    reassess?: string[];
    riskNotes?: string[];
  };
  macro?: {
    bias?: string;
    drivers?: string[];
    uncertainty?: string;
  };
  technical?: {
    trend?: string;
    keyLevels?: string[];
    volumeRead?: string;
    notes?: string[];
  };
  suggestion?: {
    action?: string;
    condition?: string;
    invalidation?: string;
    riskNotes?: string[];
  };
  tradingStructure?: {
    instId?: string;
    requestedPeriod?: string;
    period?: string;
    periodFallback?: boolean;
    source?: string;
    ts?: number;
    cacheAgeMs?: number | null;
    quality?: "complete" | "partial" | "unavailable" | string;
    warnings?: string[];
    items?: Array<{
      key?: "longShortAccountRatio" | "takerVolume" | "openInterest" | string;
      label?: string;
      value?: string;
      state?: string;
      signal?: string;
      available?: boolean;
    }>;
  };
  decision?: {
    action?: string;
    assessment?: "confirmed" | "weak_bias" | "conflict" | "insufficient" | string;
    directionLayer?: "confirmed" | "weak_bias" | "conflict" | "neutral" | string;
    direction?: "up" | "down" | "neutral" | string;
    confidence?: number;
    summary?: string;
    condition?: string;
    invalidation?: string;
    dataQuality?: "complete" | "partial" | "unavailable" | string;
    evidence?: Array<{
      key?: string;
      label?: string;
      value?: string;
      state?: string;
      signal?: string;
      available?: boolean;
    }>;
    chart?: { signal?: "up" | "down" | "neutral" | string; strength?: "confirmed" | "weak" | "neutral" | string; label?: string; gap?: string };
    evidenceGaps?: Array<{
      key?: "longShortAccountRatio" | "takerVolume" | "openInterest" | string;
      label?: string;
      value?: string;
      available?: boolean;
      state?: string;
      signal?: string;
      statusLabel?: string;
      threshold?: string;
      gap?: string;
      contribution?: string;
      upReady?: boolean;
      downReady?: boolean;
    }>;
    periods?: { chart?: string; structureRequested?: string; structureEffective?: string; structureFallback?: boolean };
  };
  confidenceExplanation?: {
    referenceValue?: number;
    referenceMeaning?: string;
    source?: string;
    sourceLabel?: string;
    sourceReason?: string;
    chartDirection?: { signal?: "up" | "down" | "neutral" | string; label?: string; gap?: string };
    confirmation?: { assessment?: "confirmed" | "weak_bias" | "conflict" | "insufficient" | string; label?: string; summary?: string };
    dataAvailability?: { quality?: "complete" | "partial" | "unavailable" | string; label?: string };
    evidence?: Array<{
      key?: "longShortAccountRatio" | "takerVolume" | "openInterest" | string;
      label?: string;
      value?: string;
      state?: string;
      available?: boolean;
      contribution?: string;
      rule?: string;
      threshold?: string;
      gap?: string;
      statusLabel?: string;
    }>;
    periods?: { chart?: string; structureRequested?: string; structureEffective?: string; structureFallback?: boolean };
  };
  observationLevels?: {
    available?: boolean;
    status?: "watch" | "unavailable" | "not_needed" | string;
    reason?: string;
    instId?: string;
    bar?: string;
    snapshotId?: string;
    snapshotTs?: number;
    dataQuality?: "complete" | "partial" | "unavailable" | string;
    partialConfirmation?: boolean;
    neutralRange?: { label?: string; low?: string; high?: string; condition?: string };
    currentState?: { status?: "watch" | string; label?: string; summary?: string };
    candidates?: Array<{
      key?: "bullish" | "bearish" | string;
      tone?: "bullish" | "bearish" | string;
      label?: string;
      confirmationPrice?: string;
      priceMeaning?: string;
      requirements?: Array<{ label?: string; detail?: string }>;
      missingEvidence?: Array<{ key?: string; label?: string; detail?: string }>;
      status?: "watch" | "awaiting_confirmation" | string;
      statusLabel?: string;
      statusDetail?: string;
      invalidationStatus?: "return_to_range_invalidates" | string;
      invalidation?: string;
    }>;
    upper?: { label?: string; price?: string; condition?: string };
    lower?: { label?: string; price?: string; condition?: string };
    returnToRange?: { label?: string; condition?: string };
    participationNote?: string;
  };
  scenarioBoard?: {
    version?: number;
    evidenceScore?: number;
    scoreMeaning?: string;
    marketState?: {
      label?: string;
      summary?: string;
      price?: string;
      rangeLow?: string;
      rangeHigh?: string;
      positionPct?: string;
      positionLabel?: string;
      strongestClue?: { label?: string; detail?: string } | null;
    };
    dataLimitations?: Array<{ label?: string; detail?: string }>;
    candidates?: Array<{
      key?: "bullish" | "bearish" | string;
      label?: string;
      tone?: "bullish" | "bearish" | string;
      status?: "confirmed" | "limited" | "watch" | string;
      statusLabel?: string;
      confirmationPrice?: string;
      priceCondition?: string;
      distance?: string;
      distanceLabel?: string;
      missingEvidence?: Array<{ key?: string; label?: string; detail?: string }>;
      limitations?: Array<{ label?: string; detail?: string }>;
      invalidation?: string;
    }>;
    snapshot?: { bar?: string; snapshotId?: string };
  };
  directionSummary?: {
    version?: number;
    headline?: "偏多观察" | "偏空观察" | "短线偏多（未确认）" | "短线偏空（未确认）" | "方向暂不可判定" | "无明确方向" | string;
    state?: "confirmed" | "watch" | "limited" | string;
    statusLabel?: string;
    direction?: "up" | "down" | "neutral" | string;
    tone?: "bullish" | "bearish" | "neutral" | string;
    reason?: string;
    metLabel?: string;
    metCondition?: string;
    missingLabel?: string;
    missingCondition?: string;
    nextCondition?: string;
    confirmationPrice?: string;
    confirmationPriceLabel?: string;
    snapshot?: { bar?: string; snapshotId?: string };
    readOnly?: string;
  };
  pricePlan?: {
    version?: number;
    entryBasis?: string;
    entryQuoteTs?: number;
    quoteSource?: string;
    instId?: string;
    bar?: string;
    source?: string;
    sourceTs?: number;
    lastClosedTs?: number;
    validUntil?: number;
    status?: "ready" | "watch" | "missed" | "expired" | "no_plan" | "unavailable" | string;
    direction?: "long" | "short" | "none" | string;
    reason?: string;
    entryPrice?: string;
    stopPrice?: string;
    targetPrice?: string;
    upperReassess?: string;
    lowerReassess?: string;
    condition?: string;
    basis?: string;
    evidence?: string[];
    bidPx?: string;
    askPx?: string;
    spread?: string;
    quoteTs?: number;
    quoteFresh?: boolean;
    priceConditionMet?: boolean;
    priceMeaning?: string;
    priceLogic?: MarketAiPriceLogic;
    costNote?: string;
    readOnly?: boolean;
  };
  multiTimeframeTrend?: {
    version?: number;
    alignment?: string;
    alignmentState?: "aligned" | "split" | "mixed" | "incomplete" | string;
    periods?: Array<{
      key?: "15m" | "1H" | "1D" | string;
      bar?: string;
      label?: string;
      available?: boolean;
      status?: "available" | "unavailable" | string;
      trend?: "up" | "down" | "range" | "volatile" | "unavailable" | string;
      trendLabel?: string;
      evidence?: string[];
      condition?: string;
      invalidation?: string;
      source?: string;
      cacheAgeMs?: number | null;
      lastCandleTs?: number;
      warning?: string;
    }>;
  };
  sources?: MarketAiSource[];
  warnings?: string[];
  cached?: boolean;
  cacheAgeMs?: number | null;
  readOnly?: boolean;
  snapshotRequired?: boolean;
  detail?: string;
  chartSnapshot?: ChartSnapshotMetadata;
};

type MarketAiVerificationSample = {
  id: string;
  reportId: string;
  instId: string;
  kind: string;
  bar: string;
  createdAt: number;
  targetTs?: number;
  dueAt: number;
  direction: string;
  status: string;
  baselineClose?: string;
  observedClose?: string;
  observedTs?: number | null;
  evaluatedAt?: number | null;
  movePct?: string;
  thresholdPct?: string;
  promptVersion?: string;
  reportSource?: string;
  reportSummary?: string;
  confidence?: number;
  entryPrice?: string;
  stopPrice?: string;
  targetPrice?: string;
  planValidUntil?: number;
  planCondition?: string;
  priceLogic?: MarketAiPriceLogic | null;
  unscoredReason?: string;
  planStatus?: string;
  planVersion?: number;
  entryBasis?: string;
  entryQuoteTs?: number | null;
  quoteSource?: string;
  priceConditionMet?: boolean | null;
  entryReferenceTouched?: boolean | null;
  stopReferenceTouched?: boolean | null;
  targetReferenceTouched?: boolean | null;
  entryReachedAfterReport?: boolean | null;
  targetReachedAfterReport?: boolean | null;
  targetAfterEntryObserved?: boolean | null;
  entryObservedAt?: number | null;
  targetObservedAt?: number | null;
  pricePathCoverage?: string | null;
  pricePathStartsAt?: number | null;
  pricePathEndsAt?: number | null;
  pricePathReportMinuteExcluded?: boolean | null;
  hypotheticalCloseReturnPct?: string | null;
};

function marketAiHypotheticalReturn(value?: string | null): { label: string; tone: "gain" | "loss" | "flat" } | null {
  if (value === null || value === undefined || value === "") return null;
  const percent = Number(value);
  if (!Number.isFinite(percent)) return null;
  if (percent > 0) return { label: `理论价差 +${percent.toFixed(2)}%`, tone: "gain" };
  if (percent < 0) return { label: `理论价差 ${percent.toFixed(2)}%`, tone: "loss" };
  return { label: "理论价差 0.00%", tone: "flat" };
}

function marketAiPlannedTargetMove(entryValue?: string, targetValue?: string, direction?: string): string | null {
  const entry = Number(entryValue);
  const target = Number(targetValue);
  if (!Number.isFinite(entry) || !Number.isFinite(target) || entry <= 0 || target <= 0 || !["long", "short"].includes(direction || "")) return null;
  const move = (target - entry) / entry * 100 * (direction === "short" ? -1 : 1);
  return `预计价差 ${move >= 0 ? "+" : ""}${move.toFixed(2)}%`;
}

function marketAiPlanEntryState(sample: MarketAiVerificationSample): { label: string; tone: string } {
  if (sample.entryBasis === "quote_snapshot" && sample.entryPrice) return { label: "分析时报价已记录 · 成交未证实", tone: "unconfirmed" };
  if (sample.status === "pending") return { label: "等待收盘核验", tone: "pending" };
  if (sample.status === "not_scored" || sample.status === "insufficient_data") return { label: "无法核验入场", tone: "unconfirmed" };
  if (sample.entryReachedAfterReport === false) return { label: "报告后未观察到入场价", tone: "unconfirmed" };
  if (sample.entryReachedAfterReport === true) return { label: "报告后曾到入场价 · 成交未证实", tone: "unconfirmed" };
  if (sample.pricePathCoverage) return { label: "报告后入场到价无法核实", tone: "unconfirmed" };
  if (sample.entryReferenceTouched === false) return { label: "未触及入场价", tone: "unconfirmed" };
  if (sample.entryReferenceTouched === true) return { label: "曾触及参考价 · 成交未证实", tone: "unconfirmed" };
  return { label: "入场未确认", tone: "unconfirmed" };
}

function marketAiTargetState(sample: MarketAiVerificationSample): string {
  if (sample.status === "pending") return "待收盘核验";
  if (sample.status === "not_scored" || sample.status === "insufficient_data") return "无法核验";
  if (sample.targetReachedAfterReport === true) return "报告后达到预测止盈价";
  if (sample.targetReachedAfterReport === false) return "可核对时段内未达到";
  if (sample.pricePathCoverage) return "报告后是否达到：数据不足";
  if (sample.targetReferenceTouched === true) return "旧记录：目标 K 线曾触价";
  if (sample.targetReferenceTouched === false) return "旧记录：目标 K 线未触及该价";
  return "报告后是否达到：无法确认";
}

function marketAiTargetSequence(sample: MarketAiVerificationSample): string {
  if (sample.entryBasis === "quote_snapshot") {
    if (sample.targetAfterEntryObserved === true) return "分析时报价在前，后续达到止盈目标价；不代表实际成交或盈利。";
    if (sample.targetAfterEntryObserved === false) return "报价后未观察到有效的止盈目标路径；请查看目标是否单独到价。";
    return "报价后的止盈路径或止损先后尚不能确认；不代表实际成交。";
  }
  if (sample.targetAfterEntryObserved === true) return "已观察到先到入场价、后到止盈价；不代表实际成交。";
  if (sample.targetAfterEntryObserved === false) return "未观察到先到入场价、后到止盈价的价格路径。";
  if (sample.pricePathCoverage) return "入场与止盈的先后顺序无法确认，不计为完成交易。";
  return "旧记录仅有整根 K 线触价观察，无法判断报告后是否到价及先后顺序。";
}

function marketAiEntryNotObserved(sample: MarketAiVerificationSample): boolean {
  if (sample.entryBasis === "quote_snapshot") return false;
  return sample.entryReachedAfterReport === false || (!sample.pricePathCoverage && sample.entryReferenceTouched === false);
}

function marketAiWatchConditionNote(conditionMet?: boolean | null, entryBasis?: string): string {
  if (entryBasis === "quote_snapshot") return "分析时的买一／卖一报价已记录，但价差偏宽或报价已过时；这只是预计入场价，不能视为成交。";
  if (conditionMet === false) return "上一根完整 15分钟 K 线尚未越过触发线。本轮只观察下一根收盘；如果到本轮截止才满足，须重新分析下一期入场价。";
  if (conditionMet === true) return "收盘突破条件已出现，但当时报价或价差尚未确认；须刷新后核对当前价格，不能把候选价视为成交。";
  return "当时尚未确认全部入场条件；旧记录未保存具体未满足项，不能据此认定可以入场。";
}

function marketAiWatchEntryLabel(conditionMet?: boolean | null, entryBasis?: string): string {
  if (entryBasis === "quote_snapshot") return "当时报价参考 · 价差或时效需复核";
  return conditionMet === false ? "收盘条件未满足，当前不能按此价入场" : conditionMet === true ? "报价或价差待确认，不能按此价直接入场" : "入场条件未核实，不能按此价直接入场";
}

function marketAiHypotheticalReturnNote(sample: MarketAiVerificationSample): string {
  if (sample.status === "pending") return "收盘后核对方向与参考价是否触及；未确认入场前不计算交易收益率。";
  const comparison = marketAiHypotheticalReturn(sample.hypotheticalCloseReturnPct);
  if (!comparison) return "缺少有效参考价或目标收盘价，无法做价格对照。";
  const pricePath = `若按 ${sample.entryPrice} ${sample.direction === "short" ? "卖出做空" : "买入做多"}、按收盘价 ${sample.observedClose} ${sample.direction === "short" ? "买回" : "卖出"}，${comparison.label}。`;
  if (sample.entryBasis === "quote_snapshot") return `入场价取分析时可见的${sample.direction === "short" ? "买一" : "卖一"}报价，未记录实际成交。${pricePath}这不是实际亏盈，未扣交易成本。`;
  if (sample.entryReachedAfterReport === false || (sample.entryReachedAfterReport == null && sample.entryReferenceTouched === false)) return `未观察到入场价，本次没有可核对的入场交易。${pricePath}这不是实际亏盈，未扣交易成本。`;
  if (sample.entryReachedAfterReport === true) return `报告后完整 1 分钟 K 线曾达到入场参考价，但不能证明成交。${pricePath}未扣交易成本。`;
  if (sample.entryReferenceTouched === true) return `整根 K 线曾触及参考价，但无法确认发生在报告后、条件满足后或实际成交。${pricePath}未扣交易成本。`;
  return `入场触价未记录，无法确认交易。${pricePath}未扣交易成本。`;
}

function MarketAiPriceLogicDetails({ logic, compact = false }: { logic: MarketAiPriceLogic; compact?: boolean }) {
  const steps = [
    ["选方向", logic.direction],
    ["定入手价", logic.entry],
    ["设止损", logic.stop],
    ["算止盈", logic.target],
    ["核验时段", logic.validity],
  ].filter((step): step is [string, string] => Boolean(step[1]));
  if (!steps.length) return null;
  return <section className={`marketAiPriceLogic ${compact ? "compact" : ""}`} aria-label="价格计算依据">
    <strong>这组价格怎么计算</strong>
    <ol>{steps.map(([label, detail]) => <li key={label}><b>{label}</b><span>{detail}</span></li>)}</ol>
  </section>;
}

type MarketAiVerificationHistory = {
  instId: string;
  scope: string;
  summary: Record<string, {
    pending: number;
    hit: number;
    miss: number;
    flat: number;
    not_scored: number;
    insufficient_data: number;
    scored: number;
    hitRatePct: number | null;
    minimumRateSamples: number;
  }>;
  samples: MarketAiVerificationSample[];
};

type MarketAiVerificationRecords = {
  samples: MarketAiVerificationSample[];
  total: number;
  limit: number;
  offset: number;
  generatedAt: number;
  readOnly: true;
  scope: string;
};

type AnnouncementType = {
  annType: string;
  annTypeDesc: string;
};

type AnnouncementTypesResponse = {
  language?: string;
  data: AnnouncementType[];
  source?: string;
  ts?: number;
  cacheAgeMs?: number | null;
  warning?: string;
};

type Announcement = {
  annType: string;
  title: string;
  url: string;
  pTime: number;
  businessPTime: number;
};

type AnnouncementsResponse = {
  language?: string;
  annType?: string;
  page: number;
  totalPage: number;
  data: Announcement[];
  source?: string;
  ts?: number;
  cacheAgeMs?: number | null;
  warning?: string;
};

type RadarScores = {
  liquidity?: number;
  tradability: number;
  volatility: number;
  riskPenalty: number;
  opportunity: number;
  dataQuality: number;
};

type RadarLiquidity = {
  value?: string;
  basis?: "quote_turnover" | "estimated_quote_turnover" | "base_volume" | "contract_volume" | "legacy_volume" | "missing" | string;
  unit?: string;
  confidence?: "high" | "medium" | "low" | string;
  displayLabel?: string;
  comparable?: boolean;
};

type RadarTurnoverWindow = {
  value?: string;
  unit?: string;
  comparable?: boolean;
  candleCount?: number;
  label?: string;
  warning?: string;
};

type RadarTurnover = {
  oneHour?: RadarTurnoverWindow;
  twentyFourHour?: RadarTurnoverWindow;
};

type RadarSortKey = "turnover_1h" | "turnover_24h";

type RadarSort = {
  key?: "turnover_1h" | "turnover_24h" | string;
  label?: string;
  candidateScope?: string;
  legacy?: boolean;
};

type RadarMetrics = {
  candleCount: number;
  recent20RangePct?: string;
  recent20ChangePct?: string;
  avgAbsReturnPct?: string;
  avgRangePct?: string;
  volumeSpike?: string;
  volume20Avg?: string;
  tickSize?: string;
  lotSize?: string;
  contractValue?: string;
};

type RadarEntryAssessment = {
  status?: "ready" | "watch" | "wait" | "avoid" | string;
  label?: string;
  confidence?: number;
  summary?: string;
  drivers?: string[];
};

type RadarMarketCondition = {
  key?: "range" | "trend" | "high_volatility" | "mixed" | "unknown" | string;
  label?: string;
  summary?: string;
};

type RadarResult = {
  instId: string;
  instFamily?: string;
  settleCcy?: string;
  state?: string;
  last?: string;
  change24hPct?: string;
  range24hPct?: string;
  volume24h?: string;
  liquidity?: RadarLiquidity;
  turnover?: RadarTurnover;
  tradabilityStatus?: "playable" | "watch_only" | "low_liquidity" | string;
  bar?: string;
  metrics: RadarMetrics;
  scores: RadarScores;
  entryAssessment?: RadarEntryAssessment;
  marketCondition?: RadarMarketCondition;
  volatilityLevel: "low" | "medium" | "high";
  riskLevel: "low" | "medium" | "high";
  tags: string[];
  reasons: string[];
  warnings: string[];
  explainedBy?: string;
  direction?: "long" | "short" | "neutral" | string;
  entryZone?: string;
};

type RadarResponse = {
  data: RadarResult[];
  rankings?: Partial<Record<RadarSortKey, RadarResult[]>>;
  filters?: Record<string, string | number | boolean>;
  sort?: RadarSort;
  summary?: {
    total: number;
    candidates: number;
    returned: number;
    explained: number;
  };
  source?: string;
  warning?: string;
  ts?: number;
  cacheAgeMs?: number | null;
};

type RadarAnalysisWatchItem = {
  instId: string;
  reason: string;
  riskNote: string;
  direction?: string;
  entryZone?: string;
};

type RadarMarketAnalysis = {
  marketRegime: "trend" | "range" | "mixed" | "risk-off" | string;
  marketBias?: "long" | "short" | "neutral" | string;
  confidence: number;
  summary: string;
  highlights: string[];
  watchlist: RadarAnalysisWatchItem[];
  riskWarnings: string[];
  suggestedFilters: string[];
  generatedAt?: number;
  source?: string;
  status?: string;
  originSource?: string;
  setupGuide?: {
    title?: string;
    description?: string;
    steps?: string[];
    requiredFields?: string[];
    providerHint?: string;
    settingsPath?: string;
  };
  warnings?: string[];
  scanTs?: number;
  cacheAgeMs?: number | null;
  marketSummary?: {
    scan?: Record<string, string | number | boolean | null>;
    breadth?: Record<string, string | number | boolean | null>;
    liquidity?: Record<string, string | number | boolean | null>;
    volatility?: Record<string, string | number | boolean | null>;
    risk?: Record<string, string | number | boolean | null>;
    sentiment?: {
      funding?: {
        sampled?: number;
        positive?: number;
        negative?: number;
        neutral?: number;
        avgFundingRate?: string;
        avgFundingRatePct?: string;
      };
      openInterest?: {
        sampled?: number;
        maxOiUsd?: string;
        medianOiUsd?: string;
      };
    };
  };
};

type RadarActionTarget = "market" | "aiOutlook" | "stats" | "trade" | "automation";

type AccountDetail = Record<string, string>;

type AutomationStrategy = {
  id: number;
  name: string;
  enabled: boolean;
  archived?: boolean;
  archived_at?: number | null;
  archived_reason?: string;
  inst_id: string;
  instIds?: string[];
  dailyPositionPct?: string;
  daily_position_pct?: string;
  bar: string;
  template: string;
  execution_mode: "signal_only" | "simulated_auto";
  td_mode: string;
  ord_type: string;
  sz: string;
  fast_window: number;
  slow_window: number;
  max_order_contracts: string;
  max_position_contracts: string;
  cooldown_seconds: number;
  take_profit_pct?: string;
  stop_loss_pct?: string;
  last_eval_ts?: number | null;
  created_at?: number;
  updated_at?: number;
};

type AutomationSignal = {
  id: number;
  strategy_id: number;
  strategy_name?: string;
  ts: number;
  environment: "simulated" | "live";
  inst_id: string;
  bar: string;
  template: string;
  action: string;
  side?: string;
  pos_side?: string;
  price?: string;
  sz?: string;
  decision: string;
  reason?: string;
  message?: string;
  raw_json?: string;
  riskSnapshot?: Record<string, unknown> | null;
  executionSteps?: Array<Record<string, unknown>>;
};

type LlmUsageLog = {
  id: number;
  request_id: string;
  ts: number;
  provider?: string;
  model?: string;
  mode?: string;
  request_type: string;
  status: string;
  strategy_id?: number | null;
  signal_id?: number | null;
  inst_id?: string | null;
  bar?: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cached_tokens: number;
  reasoning_tokens: number;
  cache_hit_tokens: number;
  cache_miss_tokens: number;
  duration_ms: number;
  timeout_seconds: number;
  finish_reason?: string;
  error?: string;
  raw_usage_json?: string;
};

type LlmUsageSummary = {
  calls: number;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cachedTokens: number;
  reasoningTokens: number;
  cacheHitTokens: number;
  cacheMissTokens: number;
  failedCalls: number;
  avgDurationMs: number;
};

type LlmUsageResponse = {
  data: LlmUsageLog[];
  summary: LlmUsageSummary;
  last24h: LlmUsageSummary;
  paging: {
    limit: number;
    offset: number;
    hasMore: boolean;
    total: number;
    page: number;
    pageCount: number;
  };
};

type AutomationStatus = {
  running: boolean;
  startedAt?: number;
  lastRunAt?: number;
  warning?: string;
  intervalSeconds: number;
  strategyCount: number;
  enabledCount: number;
  archivedCount?: number;
  globalPaused?: boolean;
  pauseReason?: string;
  pauseStartedAt?: number;
  circuitBreakerActive?: boolean;
  circuitReason?: string;
  circuitTriggeredAt?: number;
  globalStateUpdatedAt?: number;
  // 后端风控闸门新增：false 表示全局安全状态读取失败，引擎已 fail-closed 拒绝交易。
  // 字段缺失说明连接的仍是旧版后端（尚未部署加固代码）。
  globalStateAvailable?: boolean;
  alertCount?: number;
  criticalAlertCount?: number;
  // 后端 AUTOMATION_LLM_MIN_CONFIDENCE，低于该置信度不自动下单。
  llmMinConfidence?: number;
};

// 与 /api/automation/equity 对应：口径与后端每日仓位风控完全一致（只取模拟盘）。
type AutomationEquity = {
  environment?: string;
  configured?: boolean;
  available?: boolean;
  currency?: string;
  totalEq?: string;
  availEq?: string;
  equity?: string;
  equityBasis?: string;
  dailyPositionPct?: string;
  pctInvalid?: boolean;
  dailyLimit?: string;
  dailyUsed?: string;
  dailyUsedAvailable?: boolean;
  dailyRemaining?: string;
  dailyDayStart?: number;
  dailyResetAt?: number;
  source?: string;
  snapshotTs?: number;
  updatedAt?: number;
  warning?: string;
  message?: string;
};

type AutomationAlert = {
  id: number;
  ts: number;
  severity: "warning" | "critical" | string;
  source: string;
  message: string;
  strategy_id?: number | null;
  signal_id?: number | null;
  order_event_id?: number | null;
  acknowledged_at?: number | null;
  raw_json?: string;
  active?: boolean;
  raw?: Record<string, unknown> | null;
};

type AutomationRiskSnapshot = {
  id: number;
  signal_id: number;
  strategy_id: number;
  ts: number;
  allowed: boolean;
  severity: string;
  message: string;
  checks_json?: string;
  raw_json?: string;
  checks?: Array<Record<string, unknown>>;
  raw?: Record<string, unknown> | null;
};

type AutomationExecutionStep = {
  id: number;
  signal_id: number;
  strategy_id: number;
  step_order: number;
  ts: number;
  action: string;
  status: string;
  message: string;
  request_json?: string;
  response_json?: string;
  request?: Record<string, unknown>;
  response?: Record<string, unknown>;
};

type AutomationRiskCheck = {
  key: string;
  label: string;
  status: "pass" | "warn" | "block" | string;
  message: string;
  value?: string;
};

type AutomationRiskPreview = {
  allowed: boolean;
  severity: "ok" | "warning" | "blocked" | string;
  message: string;
  checks: AutomationRiskCheck[];
  signalAction?: string;
  llmConfidence?: number | null;
  minConfidence?: number;
  executionAction?: string;
  positionSide?: string;
  signal?: {
    action: string;
    price?: string | null;
    candle_ts?: number;
    reason?: string;
  };
  currentPositionContracts?: string;
  projectedPositionContracts?: string;
  orderContracts?: string;
  maxOrderContracts?: string;
  maxPositionContracts?: string;
  takeProfitPct?: string;
  stopLossPct?: string;
  cooldownRemainingSeconds?: number;
  accountSource?: string;
  updatedAt?: number;
};

type AutomationBacktestTrade = {
  side: string;
  entryTs: number;
  exitTs: number;
  entryPrice: string;
  exitPrice: string;
  contracts: string;
  pnl: string;
  returnPct: string;
  durationBars: number;
  exitReason?: string;
};

type AutomationBacktestResult = {
  ok: boolean;
  message: string;
  candles: number;
  bar?: string;
  instId?: string;
  contractValue?: string;
  initialCapital?: string;
  summary: {
    signalCount: number;
    tradeCount: number;
    winCount?: number;
    winRate: string;
    realizedPnl?: string;
    unrealizedPnl?: string;
    totalPnl: string;
    totalReturnPct: string;
    maxDrawdownPct: string;
  };
  openPosition?: null | {
    side: string;
    entryTs: number;
    entryPrice: string;
    markPrice: string;
    contracts: string;
    unrealizedPnl: string;
    returnPct: string;
    durationBars: number;
  };
  trades: AutomationBacktestTrade[];
};

type LlmConfig = {
  enabled: boolean;
  provider: string;
  baseUrl: string;
  apiKeyConfigured: boolean;
  apiKeyMasked: string;
  model: string;
  temperature: number;
  maxTokens: number;
  timeoutSeconds: number;
  effectiveTimeoutSeconds?: number;
  mode: string;
  systemPrompt: string;
  updatedAt?: number;
};

type LlmConfigForm = {
  enabled: boolean;
  providerPreset: string;
  provider: string;
  baseUrl: string;
  apiKey: string;
  clearApiKey: boolean;
  model: string;
  temperature: string;
  maxTokens: string;
  timeoutSeconds: string;
  systemPrompt: string;
};

type LlmProviderPreset = {
  key: string;
  label: string;
  provider: string;
  baseUrl: string;
  aliases?: string[];
  models: string[];
  modelNotes?: Record<string, string>;
  note: string;
  pricingNote?: string;
};

type LlmAnalysis = {
  status?: string;
  provider?: string;
  model?: string;
  mode?: string;
  prompt_version?: string;
  ts?: number;
  recommendation?: string;
  confidence?: number;
  summary?: string;
  reasons?: string[];
  risks?: string[];
  invalidation?: string;
  notes?: string;
  raw_text?: string;
  error?: string;
  usage?: Partial<LlmUsageLog>;
  usage_log_id?: number | null;
  request_id?: string;
  duration_ms?: number;
  finish_reason?: string;
};

type AutomationStrategyForm = {
  name: string;
  instId: string;
  instIds: string[];
  dailyPositionPct: string;
  bar: string;
  template: string;
  executionMode: string;
  tdMode: string;
  ordType: string;
  sz: string;
  fastWindow: string;
  slowWindow: string;
  maxPositionContracts: string;
  cooldownSeconds: string;
  takeProfitPct: string;
  stopLossPct: string;
};

type InstrumentFilter = "all" | "watch" | "usdt" | "coin" | "live";
type InstrumentSort = "default" | "change" | "volume";
type QuantityUnit = "contracts" | "base" | "quote";
type PositionSideFilter = "all" | "net" | "long" | "short";
type PositionCloseMode = "market_all" | "market_reduce" | "limit_reduce";

type SettingsStatus = {
  baseUrl: string;
  databasePath: string;
  hasCredentials: boolean;
  simulatedTrading: boolean;
  tradeEnabled?: boolean;
  tradingEnvironment?: "simulated" | "live";
  liveTradingEnabled?: boolean;
  demoHasCredentials?: boolean;
  liveHasCredentials?: boolean;
  wsPublicUrl: string;
  realtime?: {
    enabled: boolean;
    endpoint: string;
    publicTopics: string[];
    privateTopics: string[];
    automationTopics: string[];
    environment: "simulated" | "live";
    hasPrivateCredentials: boolean;
    requiresRestSnapshot: boolean;
    restFirstTopics: string[];
  };
};

type PendingOrder = {
  instId?: string;
  ordId?: string;
  clOrdId?: string;
  px?: string;
  sz?: string;
  accFillSz?: string;
  fillSz?: string;
  side?: string;
  posSide?: string;
  tdMode?: string;
  ordType?: string;
  state?: string;
  ctime?: string | number;
  utime?: string | number;
};

type SimOrderEvent = {
  id?: number;
  environment?: "simulated" | "live";
  ts?: number;
  action?: string;
  inst_id?: string;
  td_mode?: string;
  side?: string;
  pos_side?: string;
  ord_type?: string;
  px?: string;
  sz?: string;
  reduce_only?: boolean | number;
  cl_ord_id?: string;
  ord_id?: string;
  state?: string;
  code?: string;
  message?: string;
  pnl_usd?: string | null;
  pnl_pct?: string | null;
  pnl_basis?: string | null;
  pnl_gross?: string | null;
  pnl_fee?: string | null;
  pnl_settled?: boolean;
  bill_count?: number;
  pnl_note?: string | null;
  strategy_id?: number | null;
  strategy_name?: string | null;
  signal_id?: number | null;
  close_strategy_id?: number | null;
  close_strategy_name?: string | null;
  origin?: "manual" | "automation" | string | null;
};

type LeverageInfo = Record<string, string>;

type LeverageResponse = {
  configured: boolean;
  environment?: "simulated" | "live";
  data: LeverageInfo[];
  source?: string;
  message?: string;
  ts?: number;
};

type LeverageUpdateResponse = LeverageResponse & {
  ok?: boolean;
  request?: Record<string, string>;
};

type SimOrdersResponse = {
  configured: boolean;
  environment?: "simulated" | "live";
  simulatedTrading: boolean;
  tradeEnabled: boolean;
  liveTradingEnabled?: boolean;
  events: SimOrderEvent[];
  pending?: PendingOrder[];
  cacheAgeMs?: number | null;
  paging?: {
    limit: number;
    offset: number;
    hasMore: boolean;
    total: number;
    page: number;
    pageCount: number;
  };
  source?: string;
  origin?: string;
  originCounts?: {
    manual: number;
    automation: number;
    all: number;
  };
  message?: string;
  warning?: string;
  pnlSummary?: {
    pageRealizedTotal: string;
    pricedCloses: number;
    closeCount: number;
    settledCloses?: number;
  };
  ts?: number;
};

type SegmentedOption = {
  key: string;
  label: string;
  icon?: React.ReactNode;
  title?: string;
};

type NoticeTone = "info" | "warning" | "danger";

const bars = ["1m", "5m", "15m", "1H", "4H", "1D"];
const marketStatsBars = ["5m", "15m", "30m", "1H", "2H", "4H", "6H", "12H", "1D"];
const marketStatsPeriodMs: Record<string, number> = {
  "5m": 5 * 60 * 1000,
  "15m": 15 * 60 * 1000,
  "30m": 30 * 60 * 1000,
  "1H": 60 * 60 * 1000,
  "2H": 2 * 60 * 60 * 1000,
  "4H": 4 * 60 * 60 * 1000,
  "6H": 6 * 60 * 60 * 1000,
  "12H": 12 * 60 * 60 * 1000,
  "1D": 24 * 60 * 60 * 1000
};
const TICKER_POLL_MS = 15000;
const ACCOUNT_POLL_MS = 20000;
const ORDER_POLL_MS = 10000;
// 账户刷新最小间隔：WS 私有频道与 REST 轮询共用同一刷新入口，短窗口内合并，
// 避免高频 account.update/position.update 事件放大 /api/account 调用。
const ACCOUNT_REFRESH_MIN_MS = 1500;
const MAX_TRADE_INSTRUMENT_OPTIONS = 120;
const DEFAULT_LLM_TIMEOUT_SECONDS = 20;
const instrumentFilters: Array<{ key: InstrumentFilter; label: string }> = [
  { key: "usdt", label: "USDT本位" },
  { key: "live", label: "可交易" },
  { key: "watch", label: "已关注" },
  { key: "coin", label: "币本位" },
  { key: "all", label: "全部" }
];
const instrumentSorts: Array<{ key: InstrumentSort; label: string }> = [
  { key: "default", label: "默认" },
  { key: "change", label: "涨跌" },
  { key: "volume", label: "成交量" }
];
const primaryInstrumentFilters = instrumentFilters.filter((item) => item.key === "watch" || item.key === "all");
const advancedInstrumentFilters = instrumentFilters.filter((item) => item.key !== "watch" && item.key !== "all");
const tradeInstrumentFilters: Array<{ key: InstrumentFilter; label: string }> = [
  { key: "live", label: "可交易" },
  { key: "usdt", label: "USDT本位" },
  { key: "coin", label: "币本位" },
  { key: "watch", label: "自选" },
  { key: "all", label: "全部" }
];
const tradeModeOptions: SegmentedOption[] = [
  { key: "cross", label: "全仓", icon: <ShieldCheck size={14} aria-hidden="true" />, title: "全仓保证金模式" },
  { key: "isolated", label: "逐仓", icon: <ShieldAlert size={14} aria-hidden="true" />, title: "逐仓保证金模式" }
];
// 交易方向/常用类型的分段按钮不嵌图标：14px 的趋势箭头、K线、纸飞机在紧凑按钮里
// 会被挤压成难辨的怪符号（用户反馈像乱码）。只保留文字 + title 悬浮说明，选中态用底色/配色区分。
const sideOptions: SegmentedOption[] = [
  { key: "buy", label: "做多", title: "买入开多" },
  { key: "sell", label: "做空", title: "卖出开空" }
];
const reduceOnlySideOptions: SegmentedOption[] = [
  { key: "buy", label: "平空", title: "买入平空，只减仓" },
  { key: "sell", label: "平多", title: "卖出平多，只减仓" }
];
const orderTypeOptions: SegmentedOption[] = [
  { key: "limit", label: "限价", title: "按指定价格挂单" },
  { key: "market", label: "市价", title: "按市场价格立即提交" },
  { key: "post_only", label: "Post only", title: "只做 maker，无法挂单时取消" },
  { key: "ioc", label: "IOC", title: "立即成交剩余撤销" },
  { key: "fok", label: "FOK", title: "全部成交否则取消" },
  { key: "optimal_limit_ioc", label: "最优IOC", title: "OKX 最优限价 IOC" }
];
const leveragePresetOptions = [1, 2, 3, 5, 10, 20, 50, 100];
const primaryOrderTypeOptions = orderTypeOptions.slice(0, 2);
const advancedOrderTypeOptions = orderTypeOptions.slice(2);
const orderRecordActions: Array<{ key: string; label: string }> = [
  { key: "", label: "全部动作" },
  { key: "place", label: "下单" },
  { key: "close-position", label: "平仓" },
  { key: "cancel", label: "撤单" }
];
const orderRecordStates: Array<{ key: string; label: string }> = [
  { key: "", label: "全部状态" },
  { key: "accepted", label: "已提交" },
  { key: "failed", label: "失败" },
  { key: "close_requested", label: "平仓已提交" },
  { key: "cancel_requested", label: "撤单已提交" }
];
const orderRecordPageSizes = [10, 20, 50];
const tokenDisplayNames: Record<string, string> = {
  BTC: "Bitcoin",
  ETH: "Ethereum",
  SOL: "Solana",
  XRP: "XRP",
  DOGE: "Dogecoin",
  ZEC: "Zcash",
  SAND: "The Sandbox",
  SNDK: "闪迪",
  IOST: "IOST",
  PEPE: "Pepe",
  SHIB: "Shiba Inu",
  BONK: "Bonk",
  SATS: "SATS",
  ADA: "Cardano",
  AVAX: "Avalanche",
  LINK: "Chainlink",
  DOT: "Polkadot",
  LTC: "Litecoin",
  BCH: "Bitcoin Cash",
  FIL: "Filecoin",
  AAVE: "Aave",
  UNI: "Uniswap",
  OP: "Optimism",
  ARB: "Arbitrum",
  TON: "Toncoin",
  TRX: "TRON"
};
const automationTemplateOptions: SegmentedOption[] = [
  { key: "llm_direct", label: "LLM 判断", icon: <BrainCircuit size={14} aria-hidden="true" />, title: "LLM 根据历史数据直接输出做多 / 做空 / 观望" },
  { key: "ma_cross", label: "均线交叉", icon: <ChartCandlestick size={14} aria-hidden="true" /> }
];
const automationExecutionModeOptions: SegmentedOption[] = [
  { key: "signal_only", label: "只提醒", icon: <Info size={14} aria-hidden="true" />, title: "只记录信号，不自动下单" },
  { key: "simulated_auto", label: "模拟盘自动", icon: <Bot size={14} aria-hidden="true" />, title: "只允许模拟盘自动提交" }
];
const automationOrderTypeOptions: SegmentedOption[] = [
  { key: "market", label: "市价", icon: <Send size={14} aria-hidden="true" /> },
  { key: "limit", label: "限价", icon: <ChartCandlestick size={14} aria-hidden="true" /> }
];
// 周期在界面上统一显示为中文，底层仍传 1m / 5m / 15m / 1H 给后端。
const automationBarLabels: Record<string, string> = {
  "1m": "1 分钟",
  "3m": "3 分钟",
  "5m": "5 分钟",
  "15m": "15 分钟",
  "30m": "30 分钟",
  "1H": "1 小时",
  "2H": "2 小时",
  "4H": "4 小时",
  "6H": "6 小时",
  "12H": "12 小时",
  "1D": "1 天"
};

function automationBarLabel(bar?: string): string {
  const key = String(bar || "").trim();
  return automationBarLabels[key] ?? (key || "--");
}

const automationBarOptions: SegmentedOption[] = [
  { key: "5m", label: automationBarLabel("5m") },
  { key: "15m", label: automationBarLabel("15m") },
  { key: "1H", label: automationBarLabel("1H") },
  { key: "1m", label: automationBarLabel("1m"), title: "高级：频率更高，噪音和成本也更高" }
];
// 每个周期的评估上限（次/天/合约）：一天 1440 分钟 ÷ 周期分钟数。
const automationBarCadence: Record<string, { cadence: string; perDay: number }> = {
  "1m": { cadence: "每分钟", perDay: 1440 },
  "5m": { cadence: "每 5 分钟", perDay: 288 },
  "15m": { cadence: "每 15 分钟", perDay: 96 },
  "1H": { cadence: "每小时", perDay: 24 }
};
const automationStylePresets = [
  { key: "conservative", label: "稳健", fast: "10", slow: "30", cooldown: "600", note: "信号少" },
  { key: "standard", label: "标准", fast: "5", slow: "20", cooldown: "300", note: "默认" },
  { key: "responsive", label: "灵敏", fast: "3", slow: "10", cooldown: "120", note: "信号多" }
];
const signalActionFilters: SegmentedOption[] = [
  { key: "all", label: "全部", icon: <ListChecks size={14} aria-hidden="true" /> },
  { key: "long", label: "做多", icon: <TrendingUp size={14} aria-hidden="true" />, title: "快线上穿慢线产生的做多信号" },
  { key: "short", label: "做空", icon: <TrendingDown size={14} aria-hidden="true" />, title: "快线下穿慢线产生的做空信号" },
  { key: "hold", label: "观望", icon: <Info size={14} aria-hidden="true" /> }
];
const signalDecisionFilters: SegmentedOption[] = [
  { key: "all", label: "全部" },
  { key: "signal_only", label: "仅记录" },
  { key: "submitted", label: "已提交" },
  { key: "skipped", label: "已跳过" },
  { key: "blocked", label: "风控拦截" },
  { key: "llm_failed", label: "AI失败" },
  { key: "failed", label: "执行失败" },
  { key: "observed", label: "观察" }
];
const llmUsageRequestFilters: SegmentedOption[] = [
  { key: "all", label: "全部", icon: <ListChecks size={14} aria-hidden="true" /> },
  { key: "direct_signal", label: "直接信号", icon: <BrainCircuit size={14} aria-hidden="true" /> },
  { key: "signal_review", label: "信号复核", icon: <ShieldCheck size={14} aria-hidden="true" /> },
  { key: "connection_test", label: "连接测试", icon: <Info size={14} aria-hidden="true" /> }
];
const llmUsageStatusFilters: SegmentedOption[] = [
  { key: "all", label: "全部", icon: <ListChecks size={14} aria-hidden="true" /> },
  { key: "success", label: "成功", icon: <Check size={14} aria-hidden="true" /> },
  { key: "failed", label: "失败", icon: <XCircle size={14} aria-hidden="true" /> },
  { key: "timeout", label: "超时", icon: <AlertTriangle size={14} aria-hidden="true" /> }
];
const llmProviderPresets: LlmProviderPreset[] = [
  {
    key: "openai",
    label: "OpenAI",
    provider: "openai_compatible",
    baseUrl: "https://api.openai.com/v1",
    models: ["gpt-6-luna", "gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-astra"],
    modelNotes: {
      "gpt-6-luna": "GPT-6 Luna，成本最低、响应快，适合高频信号分析",
      "gpt-6.1-terra": "GPT-6.1 Terra，均衡型，支持图像输入",
      "gpt-6.1-sol": "GPT-6.1 Sol，复杂推理，成本较高",
      "gpt-6-astra": "GPT-6 Astra，旗舰推理，成本最高"
    },
    note: "官方 OpenAI 兼容接口；GPT-6 系列会自动省略温度参数（该系列不接受 temperature）。"
  },
  {
    key: "deepseek",
    label: "DeepSeek",
    provider: "openai_compatible",
    baseUrl: "https://api.deepseek.com",
    aliases: ["https://api.deepseek.com/v1"],
    models: ["deepseek-flash", "deepseek-v4-pro"],
    modelNotes: {
      "deepseek-flash": "V4.1 Flash（1017 检查点），官方当前 ID，成本低，推荐自动交易默认",
      "deepseek-v4-pro": "V4 Pro，更强推理，成本更高"
    },
    note: "DeepSeek 官方接口，当前为 V4.1 Flash / V4 Pro；系统自动启用 JSON Output 并在信号请求中关闭思考模式。",
    pricingNote: "价格以官方价目页为准，Flash 显著低于 Pro。"
  },
  {
    key: "qwen",
    label: "通义千问 Qwen",
    provider: "openai_compatible",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    models: ["qwen3.8-flash", "qwen3.7-plus", "qwen3.8-max", "qwen-long"],
    modelNotes: {
      "qwen3.8-flash": "Qwen3.8 Flash，低延迟低成本，1M 上下文",
      "qwen3.7-plus": "Qwen3.7 Plus，性价比均衡，1M 上下文",
      "qwen3.8-max": "Qwen3.8 Max，最强推理",
      "qwen-long": "超长上下文（10M），适合多周期历史"
    },
    note: "阿里云百炼兼容模式"
  },
  {
    key: "moonshot",
    label: "Kimi / Moonshot",
    provider: "openai_compatible",
    baseUrl: "https://api.moonshot.cn/v1",
    models: ["kimi-k3.1-pro", "kimi-k3.1-pro-highspeed", "kimi-k3"],
    modelNotes: {
      "kimi-k3.1-pro": "K3.1 Pro，当前旗舰，1M 上下文",
      "kimi-k3.1-pro-highspeed": "旗舰高速版，约 2~3 倍速度，价格翻倍",
      "kimi-k3": "K3，上一代旗舰，1M 上下文"
    },
    note: "Moonshot OpenAI 兼容接口；K2 系列已退役，请使用 K3 系列。"
  },
  {
    key: "openrouter",
    label: "OpenRouter",
    provider: "openai_compatible",
    baseUrl: "https://openrouter.ai/api/v1",
    models: ["openai/gpt-6-luna", "anthropic/claude-sonnet-5.5", "google/gemini-4-argon", "deepseek/deepseek-v4.1-flash"],
    modelNotes: {
      "openai/gpt-6-luna": "OpenAI GPT-6 Luna 经路由",
      "anthropic/claude-sonnet-5.5": "Claude Sonnet 5.5 经路由",
      "google/gemini-4-argon": "Gemini 4 Argon 经路由",
      "deepseek/deepseek-v4.1-flash": "DeepSeek V4.1 Flash 经路由"
    },
    note: "多模型路由，模型名以 OpenRouter 后台为准"
  },
  {
    key: "siliconflow",
    label: "SiliconFlow",
    provider: "openai_compatible",
    baseUrl: "https://api.siliconflow.cn/v1",
    models: ["deepseek-ai/DeepSeek-V4.1-Flash", "deepseek-ai/DeepSeek-V4-Pro", "Qwen/Qwen3.8-27B", "zai-org/GLM-5.3"],
    modelNotes: {
      "deepseek-ai/DeepSeek-V4.1-Flash": "V4.1 Flash 1017（10 月升级，ID 未变）",
      "deepseek-ai/DeepSeek-V4-Pro": "V4 Pro，更强推理",
      "Qwen/Qwen3.8-27B": "Qwen3.8 开源 27B",
      "zai-org/GLM-5.3": "GLM-5.3 通用模型"
    },
    note: "硅基流动 OpenAI 兼容接口，完整模型名以 /v1/models 返回为准"
  },
  {
    key: "ollama",
    label: "本地 Ollama",
    provider: "openai_compatible",
    baseUrl: "http://host.docker.internal:11434/v1",
    models: ["qwen3:8b", "llama3.2:3b", "deepseek-r1:7b"],
    note: "Docker 后端访问本机 Ollama 使用 host.docker.internal"
  },
  {
    key: "custom",
    label: "自定义兼容接口",
    provider: "custom",
    baseUrl: "",
    models: [],
    note: "手动填写 Base URL 和模型名称"
  }
];
const defaultLlmSystemPrompt = [
  "你是 OKX 永续合约的交易信号分析师，只依据输入的结构化数据判断，不编造行情或消息面。",
  "",
  "【分析框架】自上而下、按顺序综合判断，先环境后个币：",
  "0) 市场环境：先看 market_context 的 bias（risk-on/mixed/risk-off）、BTC/ETH 24h 涨跌、全市场涨跌家数占比、各赛道强弱，判断当前是顺势、逆势还是震荡环境；",
  "1) 趋势结构：MA5/MA20/MA60 的排列与价格所处位置，判定上升、下降或震荡；",
  "2) 动量位置：changePct、近 20 根高低区间与当前价在区间中的相对位置；",
  "3) 量价配合：volume20Avg 与近期量能是否支撑价格方向；",
  "4) 情绪与一致性：sentiment 的资金费率与多空倾向，与 recent_signals 的判断是否自洽。",
  "",
  "【决策原则】",
  "- 环境优先：大盘 risk-off 时对做多更谨慎、risk-on 时对做空更谨慎；个币信号与大盘方向冲突时降低置信度，并在 risks 写明冲突点。",
  "- 赛道共振：个币所属赛道明显强于或弱于大盘时，可作为方向确认的加分或减分项。",
  "- 风险优先：证据不足、多空矛盾或震荡无方向时输出 hold 并给低置信度，不为凑方向强行看多或看空。",
  "- 已有同向持仓倾向 hold 避免重复加仓；持仓方向与判断相反时在 notes 明确提示。",
  "- 置信度表示证据充分度而非预期收益：90 以上表示大盘与个币强共振且趋势明确；70-89 表示主要证据一致但有次要矛盾；50-69 表示分歧较大；低于 50 表示证据不足或互相矛盾。",
  "",
  "【输出纪律】",
  "- 只输出一个 JSON 对象，不要 Markdown 或额外解释文字。",
  "- action 只能是 long、short 或 hold。",
  "- reasons 与 risks 每条一句话并引用具体数值（大盘涨跌、赛道强弱、均线、涨跌幅、价位），不要写空话。",
  "- invalidation 必须是具体、可验证的失效条件（例如跌破 MA20 且收盘确认、价格回到某价位下方）。",
  "- 若 market_context.available 为 false，说明本次缺少大盘数据，应更保守并降低置信度。",
  "- 系统独立执行风控，仅在 OKX 模拟盘自动下单；你不直接下单，也不要声称已经下单。",
].join("\n");
const defaultLlmConfigForm: LlmConfigForm = {
  enabled: false,
  providerPreset: "openai",
  provider: "openai_compatible",
  baseUrl: "https://api.openai.com/v1",
  apiKey: "",
  clearApiKey: false,
  model: "gpt-6-luna",
  temperature: "0.2",
  maxTokens: "800",
  timeoutSeconds: String(DEFAULT_LLM_TIMEOUT_SECONDS),
  systemPrompt: defaultLlmSystemPrompt
};
const MAX_AUTOMATION_INST_IDS = 10;
const AUTOMATION_POPULAR_INST_IDS = [
  "BTC-USDT-SWAP",
  "ETH-USDT-SWAP",
  "SOL-USDT-SWAP",
  "BNB-USDT-SWAP",
  "XRP-USDT-SWAP",
  "DOGE-USDT-SWAP"
];
const defaultAutomationForm: AutomationStrategyForm = {
  name: "BTC LLM 5m 自动策略",
  instId: "BTC-USDT-SWAP",
  instIds: ["BTC-USDT-SWAP"],
  dailyPositionPct: "0",
  bar: "5m",
  template: "llm_direct",
  executionMode: "simulated_auto",
  tdMode: "cross",
  ordType: "market",
  sz: "1",
  fastWindow: "5",
  slowWindow: "20",
  maxPositionContracts: "5",
  cooldownSeconds: "300",
  takeProfitPct: "0",
  stopLossPct: "0"
};
const positionSideFilters: Array<SegmentedOption & { key: PositionSideFilter }> = [
  { key: "all", label: "全部", icon: <WalletCards size={14} aria-hidden="true" /> },
  { key: "net", label: "单向", icon: <Activity size={14} aria-hidden="true" /> },
  { key: "long", label: "多头", icon: <TrendingUp size={14} aria-hidden="true" /> },
  { key: "short", label: "空头", icon: <TrendingDown size={14} aria-hidden="true" /> }
];
const positionCloseModeOptions: Array<SegmentedOption & { key: PositionCloseMode; shortLabel: string; hint: string }> = [
  {
    key: "market_all",
    label: "市价全平",
    shortLabel: "全平",
    hint: "调用 OKX 市价全平接口，按当前可平数量全部平仓",
    icon: <XCircle size={14} aria-hidden="true" />
  },
  {
    key: "market_reduce",
    label: "市价平仓",
    shortLabel: "市价",
    hint: "填写张数，按市价提交只减仓订单",
    icon: <Send size={14} aria-hidden="true" />
  },
  {
    key: "limit_reduce",
    label: "限价平仓",
    shortLabel: "限价",
    hint: "填写张数和价格，按限价挂只减仓订单",
    icon: <ChartCandlestick size={14} aria-hidden="true" />
  }
];
const API_BASE = "";
const WS_BASE = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
const marketStatsPeriods = new Set(["5m", "15m", "30m", "1H", "2H", "4H", "6H", "12H", "1D"]);

type RealtimeEvent = {
  type: string;
  topic?: string;
  source?: string;
  environment?: "simulated" | "live";
  instId?: string;
  bar?: string;
  data?: unknown;
  message?: string;
  warning?: string;
  refreshRequired?: boolean;
  ts?: number;
  topics?: string[];
  skippedInstIds?: string[];
  activeCount?: number;
  snapshot?: ChartSnapshotMetadata;
};

type RealtimeFeedOptions = {
  enabled?: boolean;
  topics: string[];
  instId?: string;
  instIds?: string[];
  bar?: string;
  environment?: "simulated" | "live";
  onEvent?: (event: RealtimeEvent) => void;
  onSnapshotRequired?: (event: RealtimeEvent) => void;
};

function useRealtimeFeed({
  enabled = true,
  topics,
  instId,
  instIds,
  bar,
  environment,
  onEvent,
  onSnapshotRequired
}: RealtimeFeedOptions) {
  const [connected, setConnected] = React.useState(false);
  const [status, setStatus] = React.useState("等待实时连接");
  const [warning, setWarning] = React.useState("");
  const [lastEventAt, setLastEventAt] = React.useState<number | null>(null);
  const onEventRef = React.useRef(onEvent);
  const onSnapshotRequiredRef = React.useRef(onSnapshotRequired);
  const topicsKey = React.useMemo(() => topics.join("|"), [topics]);
  const instIdsKey = React.useMemo(() => (instIds ?? []).join("|"), [instIds]);

  React.useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  React.useEffect(() => {
    onSnapshotRequiredRef.current = onSnapshotRequired;
  }, [onSnapshotRequired]);

  React.useEffect(() => {
    if (!enabled || topics.length === 0) {
      setConnected(false);
      setStatus("实时连接未启用");
      return;
    }

    let closed = false;
    let socket: WebSocket | null = null;
    let reconnectTimer = 0;
    let pingTimer = 0;
    let attempt = 0;

    const subscribePayload = () => ({
      op: "subscribe",
      topics,
      instId,
      instIds,
      bar,
      environment
    });

    const connect = () => {
      socket = new WebSocket(`${WS_BASE}/ws/realtime`);
      socket.onopen = () => {
        if (closed || !socket) return;
        attempt = 0;
        setConnected(true);
        setWarning("");
        setStatus("实时通道已连接");
        socket.send(JSON.stringify(subscribePayload()));
        pingTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ op: "ping" }));
          }
        }, 20000);
      };
      socket.onmessage = (message) => {
        if (closed) return;
        const payload = JSON.parse(message.data) as RealtimeEvent;
        if (payload.type === "heartbeat" || payload.type === "pong") {
          setLastEventAt(payload.ts ?? Date.now());
          return;
        }
        setLastEventAt(payload.ts ?? Date.now());
        if (payload.type === "status") {
          setStatus(payload.message ?? "实时订阅已更新");
        }
        if (
          payload.source === "okx-ws" &&
          (payload.type === "status" || payload.type === "market.ticker" || payload.type === "market.candles")
        ) {
          setWarning("");
        }
        if (payload.type === "stale") {
          setStatus(payload.message ?? "实时通道已重连，正在刷新快照");
        }
        if (payload.type === "error" || payload.type === "disabled") {
          setWarning(payload.message ?? payload.warning ?? "实时通道暂不可用");
        }
        if (payload.refreshRequired) {
          onSnapshotRequiredRef.current?.(payload);
        }
        onEventRef.current?.(payload);
      };
      socket.onerror = () => {
        if (closed) return;
        setWarning("实时通道连接异常，已保留 REST 回退");
      };
      socket.onclose = () => {
        if (closed) return;
        window.clearInterval(pingTimer);
        setConnected(false);
        setStatus("实时通道重连中");
        attempt += 1;
        reconnectTimer = window.setTimeout(connect, Math.min(30000, 1000 * 2 ** Math.min(attempt, 5)));
      };
    };

    connect();

    return () => {
      closed = true;
      window.clearTimeout(reconnectTimer);
      window.clearInterval(pingTimer);
      socket?.close();
    };
  }, [bar, enabled, environment, instId, instIdsKey, topicsKey]);

  return { connected, status, warning, lastEventAt };
}

type MarketContractWorkspaceSnapshot = {
  selected: string;
  instruments: Instrument[];
  instrumentsLoading: boolean;
  tickers: Record<string, Ticker>;
  tickersLoading: boolean;
  tickerUpdatedAt: number | null;
  tickerSource: string;
  tickerRefresh: TickerRefresh | null;
  warning: string;
  tickerRealtime: ReturnType<typeof useRealtimeFeed>;
  chartBar: string;
  setChartBar: (bar: string) => void;
  chartCandles: Candle[];
  chartLoading: boolean;
  chartSnapshot: ChartSnapshotMetadata | null;
  refreshChartSnapshot: (force?: boolean) => Promise<ChartSnapshotMetadata | null>;
  chartSource: string;
  chartUpdatedAt: number | null;
  chartLastPushedAt: number | null;
  chartWarning: string;
  chartRealtime: ReturnType<typeof useRealtimeFeed>;
};

const MarketContractWorkspaceContext = React.createContext<MarketContractWorkspaceSnapshot | null>(null);

function useMarketContractWorkspace() {
  const snapshot = React.useContext(MarketContractWorkspaceContext);
  if (!snapshot) throw new Error("市场合约工作台上下文不可用");
  return snapshot;
}

function toCandleData(candles: Candle[]): CandlestickData[] {
  return candles.map((item) => ({
    time: Math.floor(Number(item.ts) / 1000) as Time,
    open: Number(item.open),
    high: Number(item.high),
    low: Number(item.low),
    close: Number(item.close)
  }));
}

function toVolumeData(candles: Candle[]): Array<HistogramData | { time: Time }> {
  return candles.map((item) => {
    const time = Math.floor(Number(item.ts) / 1000) as Time;
    const value = Number(item.volume);
    if (item.volume === undefined || item.volume === "" || !Number.isFinite(value) || value < 0) return { time };
    return { time, value, color: Number(item.close) >= Number(item.open) ? "#1dbf73" : "#f05d6f" };
  });
}

const RECENT_CANDLE_WINDOW = 48;

const MOVING_AVERAGES = [
  { key: "ma5", label: "MA5", period: 5, color: "#e5a823" },
  { key: "ma10", label: "MA10", period: 10, color: "#d34b78" },
  { key: "ma20", label: "MA20", period: 20, color: "#32afbf" }
] as const;

const BAR_DURATION_MS: Record<string, number> = {
  "1m": 60_000,
  "5m": 5 * 60_000,
  "15m": 15 * 60_000,
  "1H": 60 * 60_000,
  "4H": 4 * 60 * 60_000,
  "1D": 24 * 60 * 60_000
};

function chartSnapshotFreshForAnalysis(snapshot: ChartSnapshotMetadata | null): boolean {
  if (!snapshot?.snapshotId || !snapshot.complete || !snapshot.lastCandleTs) return false;
  const duration = BAR_DURATION_MS[snapshot.bar];
  return Boolean(duration && Date.now() - snapshot.lastCandleTs <= duration * 3);
}

type MovingAverageKey = (typeof MOVING_AVERAGES)[number]["key"];
type MovingAverageValues = Record<MovingAverageKey, number | null>;
type MovingAverageBundle = {
  series: Record<MovingAverageKey, LineData[]>;
  valuesByTime: Map<number, MovingAverageValues>;
};

function normalizeCandleBatch(candles: Candle[]): Candle[] {
  const byTimestamp = new Map<number, Candle>();
  candles.forEach((item) => {
    const timestamp = Math.floor(Number(item.ts));
    if (!Number.isFinite(timestamp) || timestamp <= 0) return;
    byTimestamp.set(timestamp, { ...item, ts: String(timestamp) });
  });
  return Array.from(byTimestamp.entries())
    .sort(([left], [right]) => left - right)
    .map(([, candle]) => candle);
}

function newestCandleWindow(candleCount: number) {
  const newestIndex = candleCount - 1;
  return {
    from: Math.max(0, candleCount - RECENT_CANDLE_WINDOW),
    to: Math.max(0, newestIndex) + 2
  };
}

function focusNewestCandleWindow(chart: IChartApi, candleCount: number) {
  if (candleCount <= 0) return;
  chart.timeScale().setVisibleLogicalRange(newestCandleWindow(candleCount));
  chart.timeScale().scrollToRealTime();
}

function isDegradedCandleSource(source?: string) {
  return Boolean(source?.includes("degraded"));
}

function isLiveCandleSource(source?: string) {
  return Boolean(source?.includes("ws") && !isDegradedCandleSource(source));
}

function calculateMovingAverage(candles: Candle[], period: number): LineData[] {
  const values: LineData[] = [];
  const window: number[] = [];
  let total = 0;
  candles.forEach((candle) => {
    const close = Number(candle.close);
    const time = candleChartTime(candle);
    if (!Number.isFinite(close) || time === null) {
      window.length = 0;
      total = 0;
      return;
    }
    window.push(close);
    total += close;
    if (window.length > period) total -= window.shift() ?? 0;
    if (window.length === period) values.push({ time: time as Time, value: total / period });
  });
  return values;
}

function calculateMovingAverages(candles: Candle[]): MovingAverageBundle {
  const series = Object.fromEntries(
    MOVING_AVERAGES.map((average) => [average.key, calculateMovingAverage(candles, average.period)])
  ) as Record<MovingAverageKey, LineData[]>;
  const valuesByTime = new Map<number, MovingAverageValues>();
  MOVING_AVERAGES.forEach((average) => {
    series[average.key].forEach((point) => {
      const time = Number(point.time);
      if (!Number.isFinite(time)) return;
      const current = valuesByTime.get(time) ?? { ma5: null, ma10: null, ma20: null };
      current[average.key] = point.value;
      valuesByTime.set(time, current);
    });
  });
  return { series, valuesByTime };
}

function candleCloseCountdown(candle: Candle | null | undefined, bar: string, currentMs: number) {
  if (!candle || candle.confirm === "1") return null;
  const start = Number(candle.ts);
  const duration = BAR_DURATION_MS[bar];
  if (!Number.isFinite(start) || !duration) return null;
  const remaining = start + duration - currentMs;
  return remaining > 0 && remaining <= duration ? remaining : null;
}

function formatCloseCountdown(remainingMs: number | null) {
  if (remainingMs === null) return null;
  const totalSeconds = Math.ceil(remainingMs / 1000);
  const hours = Math.floor(totalSeconds / 3_600);
  const minutes = Math.floor((totalSeconds % 3_600) / 60);
  const seconds = totalSeconds % 60;
  return hours > 0
    ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
    : `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function visibleCandleExtrema(candles: Candle[], range: LogicalRange | null) {
  if (candles.length === 0) return { high: null, low: null };
  const firstIndex = Math.max(0, Math.ceil(range?.from ?? 0));
  const lastIndex = Math.min(candles.length - 1, Math.floor(range?.to ?? candles.length - 1));
  if (firstIndex > lastIndex) return { high: null, low: null };
  let high: Candle | null = null;
  let low: Candle | null = null;
  for (let index = firstIndex; index <= lastIndex; index += 1) {
    const candle = candles[index];
    const highValue = Number(candle.high);
    const lowValue = Number(candle.low);
    if (Number.isFinite(highValue) && (!high || highValue > Number(high.high))) high = candle;
    if (Number.isFinite(lowValue) && (!low || lowValue < Number(low.low))) low = candle;
  }
  return { high, low };
}

function formatTrendNumber(value: string | number | null | undefined) {
  const numeric = Number(value);
  return Number.isFinite(numeric)
    ? numeric.toLocaleString("zh-CN", { maximumFractionDigits: 4 })
    : "--";
}

function extremaMarkers(extrema: ReturnType<typeof visibleCandleExtrema>): SeriesMarker<Time>[] {
  const highTime = candleChartTime(extrema.high);
  const lowTime = candleChartTime(extrema.low);
  if (extrema.high && extrema.low && highTime !== null && highTime === lowTime) {
    return [{
      time: highTime as Time,
      position: "belowBar",
      shape: "circle",
      color: "#617489",
      text: `高低 ${formatTrendNumber(extrema.high.high)} / ${formatTrendNumber(extrema.low.low)}`,
      size: 1
    }];
  }
  const markers: SeriesMarker<Time>[] = [];
  if (extrema.high && highTime !== null) {
    markers.push({
      time: highTime as Time,
      position: "aboveBar",
      shape: "circle",
      color: "#d34b78",
      text: `高 ${formatTrendNumber(extrema.high.high)}`,
      size: 1
    });
  }
  if (extrema.low && lowTime !== null) {
    markers.push({
      time: lowTime as Time,
      position: "aboveBar",
      shape: "circle",
      color: "#1dbf73",
      text: `低 ${formatTrendNumber(extrema.low.low)}`,
      size: 1
    });
  }
  return markers;
}

function candleChartTime(candle: Candle | null | undefined) {
  if (!candle) return null;
  const ts = Number(candle.ts);
  return Number.isFinite(ts) ? Math.floor(ts / 1000) : null;
}

function candleDelta(candle: Candle | null | undefined, previous: Candle | null | undefined) {
  const close = toNumber(candle?.close);
  const baseline = toNumber(previous?.close) ?? toNumber(candle?.open);
  if (close === null || baseline === null || baseline === 0) {
    return { absolute: null, percent: null };
  }
  const absolute = close - baseline;
  return {
    absolute,
    percent: (absolute / baseline) * 100
  };
}

function displayCandlePercent(value: number | null) {
  if (value === null || !Number.isFinite(value)) return null;
  const rounded = Number(value.toFixed(2));
  return rounded === 0 ? 0 : rounded;
}

function candleAmplitude(candle: Candle | null | undefined) {
  const high = toNumber(candle?.high);
  const low = toNumber(candle?.low);
  const open = toNumber(candle?.open);
  if (high === null || low === null || open === null || open === 0) return null;
  return ((high - low) / open) * 100;
}

function candleStateLabel(candle: Candle | null | undefined) {
  if (!candle) return "--";
  return candle.confirm === "1" ? "已收盘" : "实时更新中";
}

function formatValue(value?: string | null, fallback = "--") {
  if (value === undefined || value === null || value === "") return fallback;
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return value;
  return numeric.toLocaleString("zh-CN", { maximumFractionDigits: 4 });
}

function formatPercent(value?: string | null) {
  if (value === undefined || value === null || value === "") return "--";
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return value;
  return `${(numeric * 100).toLocaleString("zh-CN", { maximumFractionDigits: 2 })}%`;
}

function pnlValueClass(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value) || value === 0) return "pnl-neutral";
  return value > 0 ? "pnl-positive" : "pnl-negative";
}

function formatSignedValue(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "--";
  return `${value > 0 ? "+" : ""}${formatValue(String(value))}`;
}

function formatSignedPercentRatio(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "--";
  const percent = value * 100;
  return `${percent > 0 ? "+" : ""}${percent.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}%`;
}

function orderPnlNumber(value?: string | null) {
  if (value === undefined || value === null || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function formatOrderPnl(value?: string | null) {
  const numeric = orderPnlNumber(value);
  if (numeric === null) return "--";
  return `${numeric > 0 ? "+" : ""}${numeric.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function formatOrderPnlPct(value?: string | null) {
  const numeric = orderPnlNumber(value);
  if (numeric === null) return "";
  return `${numeric > 0 ? "+" : ""}${numeric.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
  })}%`;
}

function orderPnlBasisLabel(basis?: string | null) {
  if (basis === "okx-bills-settled") return "OKX 已结算（含手续费）";
  if (basis === "okx-upl") return "实时持仓快照";
  if (basis === "cached-upl") return "平仓前持仓快照";
  if (basis === "signal-snapshot") return "信号留存快照";
  if (basis === "position-snapshot") return "历史持仓快照";
  if (basis === "estimated-price") return "价格估算";
  return "";
}

function toNumber(value?: string | null) {
  if (value === undefined || value === null || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function decimalPlaces(value?: string | null) {
  if (!value) return 0;
  const text = String(value).toLowerCase();
  if (text.includes("e-")) {
    const [, exponent] = text.split("e-");
    return Number(exponent) || 0;
  }
  const [, decimals = ""] = text.split(".");
  return decimals.replace(/0+$/, "").length;
}

function floorToStep(value: number, step: number, stepText?: string | null) {
  if (!Number.isFinite(value) || value <= 0) return 0;
  if (!Number.isFinite(step) || step <= 0) return value;
  const rounded = Math.floor(value / step + 1e-12) * step;
  const digits = Math.min(Math.max(decimalPlaces(stepText), 0), 12);
  return Number(rounded.toFixed(digits));
}

function formatMarketNumber(value?: string | number | null, fallback = "--") {
  if (value === undefined || value === null || value === "") return fallback;
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  const abs = Math.abs(numeric);
  const digits = abs >= 100 ? 2 : abs >= 1 ? 4 : 8;
  return numeric.toLocaleString("zh-CN", { maximumFractionDigits: digits });
}

function formatOrderNumber(value?: number | null, maxDigits = 8) {
  if (value === undefined || value === null || !Number.isFinite(value)) return "--";
  const fixed = value.toFixed(maxDigits);
  return fixed.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
}

function instrumentCurrencies(instId: string) {
  const [base = "--", quote = "--"] = instId.toUpperCase().split("-");
  return { base, quote };
}

function quantityUnitLabel(unit: QuantityUnit, instId: string) {
  const { base, quote } = instrumentCurrencies(instId);
  if (unit === "contracts") return "张";
  if (unit === "base") return base;
  return quote;
}

function isLinearSwap(instrument: Instrument | undefined, instId: string) {
  const quote = instrumentCurrencies(instId).quote;
  return instrument?.settle_ccy === "USDT" || instrument?.settle_ccy === "USDC" || quote === "USDT" || quote === "USDC";
}

function contractValueCurrency(instrument: Instrument | undefined, instId: string) {
  const ccy = String(instrument?.ct_val_ccy || "").toUpperCase();
  if (ccy) return ccy;
  const { base, quote } = instrumentCurrencies(instId);
  return isLinearSwap(instrument, instId) ? base : quote;
}

function contractValueLabel(instrument: Instrument | undefined, instId: string) {
  if (!instrument?.ct_val) return "--";
  const ccy = contractValueCurrency(instrument, instId);
  return ccy ? `${instrument.ct_val} ${ccy}` : instrument.ct_val;
}

function instrumentSettlementCurrency(instrument: Instrument | undefined, instId: string) {
  const settle = String(instrument?.settle_ccy || "").toUpperCase();
  if (settle) return settle;
  return instrumentCurrencies(instId).quote;
}

function instrumentSettlementKind(instrument: Instrument | undefined, instId: string) {
  const settle = instrumentSettlementCurrency(instrument, instId);
  if (settle === "USDT" || settle === "USDC") return "usdt";
  if (settle) return "coin";
  return "unknown";
}

function instrumentSettlementLabel(instrument: Instrument | undefined, instId: string) {
  const settle = instrumentSettlementCurrency(instrument, instId);
  if (settle === "USDT" || settle === "USDC") return `${settle}本位`;
  if (settle) return `币本位 ${settle}结算`;
  return "币本位";
}

function instrumentSummaryLabel(instrument: Instrument | undefined, instId: string) {
  return `${instrument?.inst_family ?? "SWAP"} · ${instrumentSettlementLabel(instrument, instId)} · 面值 ${contractValueLabel(instrument, instId)}`;
}

function instrumentBaseToken(instId: string) {
  return instrumentCurrencies(instId).base.replace(/[^A-Z0-9]/g, "");
}

function normalizedTokenNameKey(token: string) {
  return token.replace(/^\d+/, "");
}

function instrumentDisplaySymbol(instId: string) {
  const { base, quote } = instrumentCurrencies(instId);
  if (!base || base === "--") return instId.replace(/-/g, "");
  if (!quote || quote === "--") return base;
  return `${base}${quote}`;
}

function instrumentAssetName(instrument: Instrument | undefined, instId: string) {
  const base = instrumentBaseToken(instId);
  const normalized = normalizedTokenNameKey(base);
  return tokenDisplayNames[base] ?? tokenDisplayNames[normalized] ?? instrument?.inst_family?.replace(/-USDT$/i, "") ?? base;
}

function instrumentContractTypeLabel(instrument: Instrument | undefined, instId: string) {
  const type = String(instrument?.inst_type || "").toUpperCase();
  if (type === "SWAP" || instId.toUpperCase().endsWith("-SWAP")) return "永续";
  if (type === "FUTURES") return "交割";
  if (type === "OPTION") return "期权";
  return type || "合约";
}

function market24hActivity(ticker: Ticker | null | undefined, instId: string) {
  const { base, quote } = instrumentCurrencies(instId);
  const quoteValue = toNumber(ticker?.volCcyQuote24h);
  const baseValue = toNumber(ticker?.volCcy24h);
  const contractValue = toNumber(ticker?.vol24h);
  if (quoteValue !== null && quoteValue >= 0) {
    return { label: `24h 成交额（${quote}）`, value: formatCompact(quoteValue), unit: quote };
  }
  if (baseValue !== null && baseValue >= 0) {
    return { label: `24h 成交量（${base}）`, value: formatCompact(baseValue), unit: base };
  }
  if (contractValue !== null && contractValue >= 0) {
    return { label: "24h 成交量（张）", value: formatCompact(contractValue), unit: "张" };
  }
  return { label: "24h 成交量", value: "--", unit: "" };
}

function instrumentActivityLabel(ticker: Ticker | null | undefined, instId: string) {
  const turnover = instrumentQuoteTurnover(ticker);
  if (turnover === null || turnover <= 0) return "24h 成交额 --";
  const { quote } = instrumentCurrencies(instId);
  return `24h 额 ${formatCompact(turnover)}${quote ? ` ${quote}` : ""}`;
}

function instrumentAvatarText(instId: string) {
  const base = instrumentBaseToken(instId);
  if (!base) return "--";
  if (base === "BTC") return "B";
  if (base === "ETH") return "E";
  if (base === "SOL") return "S";
  return base.slice(0, 2);
}

// OKX 永续 ticker 没有 volCcyQuote24h：volCcy24h 是基础币数量、vol24h 是张数，
// 单位随合约面值而变（SATS 的 6e13 个币只值几十万美元）。跨合约比较与排序前
// 必须统一换算成计价币名义成交额，否则低价 meme 币会凭数字量级霸榜。
function instrumentQuoteTurnover(
  ticker: Ticker | null | undefined,
  instrument?: Instrument
): number | null {
  const quoteValue = toNumber(ticker?.volCcyQuote24h);
  if (quoteValue !== null && Number.isFinite(quoteValue) && quoteValue >= 0) return quoteValue;
  const last = toNumber(ticker?.last);
  const price = last !== null && Number.isFinite(last) && last > 0 ? last : null;
  const baseValue = toNumber(ticker?.volCcy24h);
  if (price !== null && baseValue !== null && Number.isFinite(baseValue) && baseValue >= 0) {
    return baseValue * price;
  }
  const contractVolume = toNumber(ticker?.vol24h);
  const contractValue = toNumber(instrument?.ct_val);
  if (
    price !== null &&
    contractVolume !== null && Number.isFinite(contractVolume) && contractVolume >= 0 &&
    contractValue !== null && Number.isFinite(contractValue) && contractValue > 0
  ) {
    return contractVolume * contractValue * price;
  }
  return null;
}

function relevanceRank(value: number | null | undefined) {
  return value === null || value === undefined || !Number.isFinite(value) ? -Infinity : value;
}

function compareInstrumentRelevance(
  left: Instrument,
  right: Instrument,
  options: {
    selectedInstId?: string;
    sortMode: InstrumentSort;
    tickers: Record<string, Ticker>;
  }
) {
  const selectedInstId = options.selectedInstId?.toUpperCase() ?? "";
  if (left.inst_id === selectedInstId) return -1;
  if (right.inst_id === selectedInstId) return 1;

  // 用户显式选择「涨跌 / 成交量」时严格按该指标排，不再被关注状态或结算币种插队。
  const explicitSort = options.sortMode !== "default";
  if (!explicitSort && Boolean(left.watched) !== Boolean(right.watched)) {
    return left.watched ? -1 : 1;
  }

  const leftTicker = options.tickers[left.inst_id];
  const rightTicker = options.tickers[right.inst_id];
  const leftChange = relevanceRank(tickerTodayChange(leftTicker).percent);
  const rightChange = relevanceRank(tickerTodayChange(rightTicker).percent);
  const leftTurnover = relevanceRank(instrumentQuoteTurnover(leftTicker, left));
  const rightTurnover = relevanceRank(instrumentQuoteTurnover(rightTicker, right));

  // 完全没有行情的合约统一沉底；用比较而非相减，避免 -Infinity - -Infinity 得到 NaN
  // 让 Array.sort 把顺序判为「相等」而出现抖动。
  const leftMissing = leftTurnover === -Infinity && leftChange === -Infinity;
  const rightMissing = rightTurnover === -Infinity && rightChange === -Infinity;
  if (leftMissing !== rightMissing) return leftMissing ? 1 : -1;

  if (options.sortMode === "change" && leftChange !== rightChange) {
    return rightChange > leftChange ? 1 : -1;
  }
  if (options.sortMode === "volume" && leftTurnover !== rightTurnover) {
    return rightTurnover > leftTurnover ? 1 : -1;
  }

  if (!explicitSort) {
    const leftSettlement = instrumentSettlementKind(left, left.inst_id);
    const rightSettlement = instrumentSettlementKind(right, right.inst_id);
    if (leftSettlement !== rightSettlement) {
      if (leftSettlement === "usdt") return -1;
      if (rightSettlement === "usdt") return 1;
      return leftSettlement.localeCompare(rightSettlement);
    }
    const leftLive = left.state === "live" ? 0 : 1;
    const rightLive = right.state === "live" ? 0 : 1;
    if (leftLive !== rightLive) return leftLive - rightLive;
  }

  if (leftTurnover !== rightTurnover) {
    return rightTurnover > leftTurnover ? 1 : -1;
  }
  return left.inst_id.localeCompare(right.inst_id);
}

function contractsToAmounts(contracts: number, instrument: Instrument | undefined, instId: string, price: number | null) {
  const ctVal = toNumber(instrument?.ct_val);
  const { base, quote } = instrumentCurrencies(instId);
  if (!ctVal || !Number.isFinite(contracts) || contracts <= 0) {
    return { base, quote, baseAmount: null, quoteAmount: null };
  }
  if (isLinearSwap(instrument, instId)) {
    const baseAmount = contracts * ctVal;
    return {
      base,
      quote,
      baseAmount,
      quoteAmount: price ? baseAmount * price : null
    };
  }
  const quoteAmount = contracts * ctVal;
  return {
    base,
    quote,
    baseAmount: price ? quoteAmount / price : null,
    quoteAmount
  };
}

function contractsFromQuantity(
  input: string,
  unit: QuantityUnit,
  instrument: Instrument | undefined,
  instId: string,
  price: number | null
) {
  const value = toNumber(input);
  if (value === null || value <= 0) {
    return { error: "下单数量必须大于 0。" };
  }
  const ctVal = toNumber(instrument?.ct_val);
  const lotSz = toNumber(instrument?.lot_sz) ?? 0;
  if (unit !== "contracts" && (!ctVal || ctVal <= 0)) {
    return { error: "当前合约缺少面值，无法换算数量。" };
  }

  let rawContracts = value;
  if (unit === "base") {
    if (!ctVal) return { error: "当前合约缺少面值，无法换算标的币数量。" };
    if (isLinearSwap(instrument, instId)) {
      rawContracts = value / ctVal;
    } else {
      if (!price || price <= 0) return { error: "币本位合约按标的币下单需要有效价格。" };
      rawContracts = (value * price) / ctVal;
    }
  }
  if (unit === "quote") {
    if (!ctVal) return { error: "当前合约缺少面值，无法换算计价金额。" };
    if (isLinearSwap(instrument, instId)) {
      if (!price || price <= 0) return { error: "按计价金额下单需要有效价格。" };
      rawContracts = value / (ctVal * price);
    } else {
      rawContracts = value / ctVal;
    }
  }

  const contracts = floorToStep(rawContracts, lotSz, instrument?.lot_sz);
  if (!contracts || contracts <= 0) {
    return { error: `换算后小于最小下单 ${instrument?.lot_sz ?? "--"} 张。` };
  }
  const amounts = contractsToAmounts(contracts, instrument, instId, price);
  return {
    contracts,
    contractsText: formatOrderNumber(contracts, Math.max(decimalPlaces(instrument?.lot_sz), 8)),
    ...amounts
  };
}

function minimumQuantityForUnit(unit: QuantityUnit, instrument: Instrument | undefined, instId: string, price: number | null) {
  const lotSz = toNumber(instrument?.lot_sz);
  if (!lotSz || lotSz <= 0) return "";
  if (unit === "contracts") return instrument?.lot_sz ?? formatOrderNumber(lotSz);
  const amounts = contractsToAmounts(lotSz, instrument, instId, price);
  if (unit === "base") return formatOrderNumber(amounts.baseAmount, 8);
  return formatOrderNumber(amounts.quoteAmount, 8);
}

function formatCompact(value?: string | number | null, fallback = "--") {
  if (value === undefined || value === null || value === "") return fallback;
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  return numeric.toLocaleString("zh-CN", {
    notation: "compact",
    maximumFractionDigits: 2
  });
}

function tickerValue(ticker: Ticker | null | undefined, keys: string[]) {
  const key = keys.find((item) => ticker?.[item] !== undefined && ticker?.[item] !== "");
  return key ? ticker?.[key] : undefined;
}

function tickerChangeFromBases(ticker: Ticker | null | undefined, baseKeys: string[]) {
  const last = toNumber(ticker?.last);
  const base = baseKeys
    .map((key) => toNumber(ticker?.[key]))
    .find((value): value is number => value !== null && value !== 0);
  if (last === null || base === undefined) {
    return { absolute: null, percent: null };
  }
  const absolute = last - base;
  return {
    absolute,
    percent: (absolute / base) * 100
  };
}

function tickerTodayChange(ticker: Ticker | null | undefined) {
  return tickerChangeFromBases(ticker, ["sodUtc8"]);
}

function tickerRolling24hChange(ticker: Ticker | null | undefined) {
  return tickerChangeFromBases(ticker, ["open24h"]);
}

function formatSigned(value: number | null, suffix = "", maximumFractionDigits = Math.abs(value ?? 0) >= 1 ? 2 : 4) {
  if (value === null) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString("zh-CN", { maximumFractionDigits })}${suffix}`;
}

function formatSignedPercent(value: number | null) {
  return formatSigned(value, "%", 2);
}

function changeClass(value: number | null | undefined) {
  return value === undefined || value === null || value >= 0 ? "up" : "down";
}

function stateLabel(state?: string) {
  if (state === "live") return "可交易";
  if (state === "suspend") return "暂停";
  if (state === "preopen") return "预开";
  return state ?? "--";
}

function sourceLabel(source?: string) {
  if (!source) return "等待数据";
  if (source === "initializing") return "初始化中";
  if (source === "backend") return "服务端";
  if (source === "okx-unavailable") return "OKX 异常";
  if (source === "okx-announcements") return "OKX 公告";
  if (source === "okx-announcement-types") return "OKX 分类";
  if (source === "announcement-types-default") return "默认分类";
  if (source.includes("announcements") || source.includes("announcement-types")) {
    if (source.includes("unavailable")) return "公告不可用";
    if (source.includes("stale") || source.includes("cache")) return "公告缓存";
    return "公告数据";
  }
  if (source.includes("market-stats")) {
    if (source.includes("partial")) return "统计部分可用";
    if (source.includes("stale") || source.includes("cache")) return "统计缓存";
    return "交易统计";
  }
  if (source === "llm-market-ai-outlook") return "AI分析";
  if (source === "market-ai-cache") return "AI缓存";
  if (source === "llm-market-analysis") return "LLM";
  if (source === "llm-not-configured") return "未配置";
  if (source === "metric-fallback") return "指标降级";
  if (source === "partial-fallback") return "部分回退";
  if (source === "radar-analysis-cache") return "分析缓存";
  if (source.includes("degraded")) return "数据待补齐";
  if (source.includes("ws")) return "OKX WS";
  if (source.includes("cache")) return "缓存";
  if (source.includes("rest")) return "OKX REST";
  return source;
}

function tickerRefreshStatus(refresh?: TickerRefresh | null, realtimeConnected = false) {
  const state = refresh?.state ?? "fresh";
  if (state === "fresh") return null;
  if (state === "unavailable" || state === "initializing") {
    return {
      pill: state === "initializing" ? "列表初始化" : "列表不可用",
      detail: refresh?.label ?? "行情列表暂不可用，正在等待完整行情快照。"
    };
  }
  const snapshotTime = refresh?.snapshotTs ? new Date(refresh.snapshotTs).toLocaleTimeString("zh-CN") : "--";
  const nextStep = realtimeConnected ? "所选合约价格仍在实时更新" : "所选合约价格正在重连";
  const pill = state === "backing_off" ? "列表快照 · 自动重试" : state === "refreshing" ? "列表快照 · 后台刷新" : "列表快照";
  return {
    pill,
    detail: `${refresh?.label ?? "行情列表暂沿用最近完整快照"} · 快照 ${snapshotTime} · ${nextStep}`
  };
}

function compactRealtimeWarning(message?: string, topic?: string) {
  const text = (message ?? "").trim();
  if (!text) return "";
  if (text.includes("60018") || text.includes("wrong URL") || text.includes("doesn't exist")) {
    if (topic === "market.ticker") {
      return "部分价格实时订阅失败，已保留 REST/缓存快照。";
    }
    return "K线实时订阅失败，已保留 REST/缓存快照。";
  }
  // Transport and upstream exceptions are diagnostic details, not user-facing status copy.
  if (!/[\u3400-\u9fff]/u.test(text) || /websocket|connection|nonetype|resume_reading|traceback|exception|timed? out|\berror\b|\bfailed\b/i.test(text)) {
    if (topic === "market.ticker") return "价格实时连接暂不可用，系统正在自动重连。";
    if (topic === "market.candles") return "K线数据暂未更新，系统正在自动重试。";
    return "行情列表暂未更新，系统正在自动重试。";
  }
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
}

function isTransientMarketWsError(message?: string) {
  const text = (message ?? "").toLowerCase();
  return (
    text.includes("opening handshake") ||
    text.includes("timed out") ||
    text.includes("connection failed") ||
    text.includes("connection closed")
  );
}

function announcementTypeLabel(types: AnnouncementType[], annType?: string) {
  if (!annType) return "全部公告";
  return types.find((item) => item.annType === annType)?.annTypeDesc ?? annType;
}

function effectiveMarketStatsPeriod(bar: string) {
  return marketStatsPeriods.has(bar) ? bar : "5m";
}

function nextMarketStatsRefreshDelay(period: string) {
  const interval = marketStatsPeriodMs[period] ?? marketStatsPeriodMs["5m"];
  const now = Date.now();
  return interval - (now % interval) + 2500;
}

function marketStatsRatioClass(value?: string) {
  const numeric = toNumber(value);
  if (numeric === null) return "";
  return numeric >= 1 ? "up" : "down";
}

function marketStatsSignedClass(value?: string) {
  const numeric = toNumber(value);
  if (numeric === null) return "";
  return numeric >= 0 ? "up" : "down";
}

function marketStatsBuyShareClass(value?: string) {
  const numeric = toNumber(value);
  if (numeric === null) return "";
  return numeric >= 50 ? "up" : "down";
}

function longShortBiasLabel(value?: string) {
  if (value === "more_long_accounts") return "净多账户较多";
  if (value === "more_short_accounts") return "净空账户较多";
  if (value === "balanced_accounts") return "多空账户接近";
  return "暂无多空人数";
}

function takerDominanceLabel(value?: string) {
  if (value === "active_buying_stronger") return "主动买入占优";
  if (value === "active_selling_stronger") return "主动卖出占优";
  if (value === "balanced_taker_flow") return "主动买卖接近";
  return "暂无主动买卖";
}

function openInterestTrendLabel(value?: string) {
  if (value === "increasing") return "持仓增加";
  if (value === "decreasing") return "持仓减少";
  if (value === "flat") return "持仓平稳";
  return "暂无持仓变化";
}

function formatStatsCompact(value?: string | null, unit = "") {
  if (!value) return "--";
  const formatted = formatCompact(value);
  return unit ? `${formatted} ${unit}` : formatted;
}

function formatStatsPercentPoint(value?: string | null) {
  return formatPercentPoint(value);
}

function longShortAccountShares(value?: string | null) {
  const ratio = toNumber(value);
  if (ratio === null || ratio < 0) return { longPct: null, shortPct: null };
  const total = ratio + 1;
  if (total <= 0) return { longPct: null, shortPct: null };
  return {
    longPct: (ratio / total) * 100,
    shortPct: (1 / total) * 100
  };
}

function formatStatsShare(value: number | null) {
  if (value === null || !Number.isFinite(value)) return "--";
  return `${value.toLocaleString("zh-CN", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

function recentMarketStatsPoints<T>(points: T[] | undefined, count = 4) {
  return (points ?? []).slice(-count).reverse();
}

function formatPointTime(ts?: number) {
  if (!ts) return "--";
  return new Date(ts).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function marketStatsWarningLabel(value: string) {
  return value
    .replace("OKX response was incomplete after retries: IncompleteRead(0 bytes read)", "OKX 本次返回中断，已重试")
    .replace(/OKX response was incomplete after retries: /g, "OKX 本次返回中断：");
}

function marketAiStanceLabel(value?: string) {
  if (value === "bullish") return "偏多参考";
  if (value === "bearish") return "偏空参考";
  if (value === "wait") return "暂时观望";
  return "中性观察";
}

function marketAiStanceClass(value?: string) {
  if (value === "bullish") return "up";
  if (value === "bearish") return "down";
  if (value === "wait") return "warning";
  return "";
}

function marketAiActionLabel(value?: string) {
  if (value === "consider_long") return "偏多参考";
  if (value === "consider_short") return "偏空参考";
  if (value === "wait_release") return "暂不形成方向";
  if (value === "avoid") return "降低关注";
  return "继续阅读";
}

function marketAiActionExplanation(value?: string) {
  if (value === "wait_release") return "图表与交易结构尚未同时给出可靠方向；当前仅观察，不作为买卖信号。";
  return "这是基于本次图表快照的阅读参考，不作为买卖信号。";
}

function marketAiDirectionLayerLabel(decision?: MarketAiOutlookResponse["decision"]) {
  if (decision?.directionLayer === "confirmed") return marketAiActionLabel(decision.action);
  if (decision?.directionLayer === "weak_bias") return decision.direction === "up" ? "短线略偏多 · 待确认" : decision.direction === "down" ? "短线略偏空 · 待确认" : "弱偏向 · 待确认";
  if (decision?.directionLayer === "conflict") return "多空信号分歧";
  return "中性观望";
}

function marketAiDirectionLayerExplanation(decision?: MarketAiOutlookResponse["decision"]) {
  if (decision?.directionLayer === "weak_bias") return "已有轻微图表偏向，但未达到完整结构确认；仅供继续观察，不作为买卖信号。";
  if (decision?.directionLayer === "conflict") return "可用证据指向不同方向；当前只展示分歧与重读条件，不作为买卖信号。";
  if (decision?.directionLayer === "neutral") return "数据已获取，但目前均处于中性或临界区；等待价格与结构出现同向变化。";
  return marketAiActionExplanation(decision?.action);
}

function marketAiDecisionAssessmentLabel(value?: string) {
  if (value === "confirmed") return "结构确认";
  if (value === "weak_bias") return "弱偏向待确认";
  if (value === "conflict") return "信号分歧";
  return "中性观望";
}

function marketAiDataQualityLabel(value?: string) {
  if (value === "complete") return "交易数据已获取";
  if (value === "partial") return "交易数据部分可用";
  return "交易数据待确认";
}

type MarketAiStructureItem = NonNullable<NonNullable<MarketAiOutlookResponse["tradingStructure"]>["items"]>[number];

function marketAiStructureLabel(item?: MarketAiStructureItem) {
  if (item?.key === "openInterest") return "市场总持仓增减";
  return item?.label || "交易结构数据";
}

function marketAiStructureStateLabel(item?: MarketAiStructureItem) {
  if (!item?.available) return "暂未获取 · 不参与本次判断";
  if (item.key === "longShortAccountRatio") return longShortBiasLabel(item.state);
  if (item.key === "takerVolume") return takerDominanceLabel(item.state);
  if (item.key === "openInterest") return openInterestTrendLabel(item.state);
  return item.state || "待确认";
}

function marketAiStructureValue(item?: MarketAiStructureItem) {
  if (!item?.available) return "--";
  if (item.key === "takerVolume" || item.key === "openInterest") return item.value ? formatPercentPoint(item.value) : "--";
  return formatValue(item.value);
}

function marketAiStructureExplanation(item?: MarketAiStructureItem) {
  if (item?.key !== "openInterest") return "";
  return item.available
    ? "反映市场未平仓合约的增减，不是个人持仓。"
    : "不是 0，也不代表没有市场持仓。";
}

function marketAiHorizonLabel(value?: string) {
  if (value === "15m") return "未来 15 分钟";
  if (value === "1h") return "未来 1 小时";
  if (value === "today") return "今日";
  return value || "时间视角";
}

function marketAiConfidence(outlook: MarketAiOutlookResponse | null) {
  return outlook?.overall?.confidence ?? outlook?.confidence ?? 0;
}

function marketAiConfidenceExplanation(outlook: MarketAiOutlookResponse | null) {
  const decision = outlook?.decision;
  const structure = outlook?.tradingStructure;
  if (outlook?.confidenceExplanation) return outlook.confidenceExplanation;
  const isFallback = outlook?.source === "metric-fallback";
  return {
    referenceValue: decision?.confidence ?? marketAiConfidence(outlook),
    referenceMeaning: "表示本次行情阅读的证据充分程度，不代表价格涨跌概率或收益结果。",
    sourceLabel: isFallback ? "指标降级" : "报告依据",
    sourceReason: isFallback ? "本次报告使用规则化指标解读。" : "本次报告依据当前图表快照与交易结构证据生成。",
    chartDirection: {
      signal: outlook?.technical?.trend,
      label: outlook?.technical?.trend ? `图表结构：${marketAiTrendLabel(outlook.technical.trend)}` : "图表方向待确认",
      gap: "旧报告未附图表方向缺口；刷新后可查看。"
    },
    confirmation: {
      assessment: decision?.assessment,
      label: marketAiDecisionAssessmentLabel(decision?.assessment),
      summary: decision?.summary
    },
    dataAvailability: {
      quality: decision?.dataQuality ?? structure?.quality,
      label: marketAiDataQualityLabel(decision?.dataQuality ?? structure?.quality)
    },
    evidence: (structure?.items ?? []).slice(0, 3).map((item) => ({
      ...item,
      contribution: item.available ? "旧报告未附本次确认说明" : "未获取，不参与本次判断",
      rule: "查看当前交易结构状态，不把数据可用性等同于方向确认。"
    }))
  };
}

function marketAiConfidenceEvidenceValue(item?: NonNullable<NonNullable<MarketAiOutlookResponse["confidenceExplanation"]>["evidence"]>[number]) {
  if (!item?.available) return "--";
  if (item.key === "takerVolume" || item.key === "openInterest") return item.value ? formatPercentPoint(item.value) : "--";
  return formatValue(item?.value);
}

type MarketAiEvidenceGap = NonNullable<NonNullable<MarketAiOutlookResponse["decision"]>["evidenceGaps"]>[number];

function marketAiEvidenceGaps(outlook: MarketAiOutlookResponse | null): MarketAiEvidenceGap[] {
  const direct = outlook?.decision?.evidenceGaps;
  if (direct?.length) return direct;
  return (outlook?.confidenceExplanation?.evidence ?? []).map((item) => ({
    ...item,
    statusLabel: item.statusLabel || marketAiStructureStateLabel(item),
    threshold: item.threshold || item.rule,
    gap: item.gap || "旧报告未附与门槛的差距；刷新后可查看。"
  }));
}

function marketAiPeriodProvenance(outlook: MarketAiOutlookResponse | null) {
  const periods = outlook?.decision?.periods ?? outlook?.confidenceExplanation?.periods;
  const chart = periods?.chart || outlook?.chartSnapshot?.bar || "当前";
  const requested = periods?.structureRequested || outlook?.tradingStructure?.requestedPeriod || chart;
  const effective = periods?.structureEffective || outlook?.tradingStructure?.period || "--";
  const fallback = periods?.structureFallback ?? outlook?.tradingStructure?.periodFallback;
  return {
    chart,
    requested,
    effective,
    fallback: Boolean(fallback),
    label: fallback ? `图表 ${chart} · 交易结构统计 ${effective}（${requested} 不可用）` : `图表 ${chart} · 交易结构统计 ${effective}`
  };
}

type MarketAiObservationLevels = NonNullable<MarketAiOutlookResponse["observationLevels"]>;
type MarketAiConfirmationCandidate = NonNullable<MarketAiObservationLevels["candidates"]>[number];

function marketAiConfirmationLevels(levels?: MarketAiObservationLevels) {
  if (!levels?.available || !levels.neutralRange) return null;
  const candidates = (levels.candidates ?? []).filter((candidate): candidate is MarketAiConfirmationCandidate => Boolean(candidate?.confirmationPrice));
  if (candidates.length >= 2) {
    return {
      currentState: levels.currentState ?? {
        status: "watch",
        label: "当前：保持观望",
        summary: levels.neutralRange.condition || "价格仍在本次区间内，当前保持观望。"
      },
      candidates: candidates.slice(0, 2)
    };
  }
  if (!levels.upper?.price || !levels.lower?.price) return null;
  const invalidation = levels.returnToRange?.condition || "突破后回到原区间，恢复观望。";
  return {
    currentState: {
      status: "watch",
      label: "当前：保持观望",
      summary: levels.neutralRange.condition || "价格仍在本次区间内，当前保持观望。"
    },
    candidates: [
      {
        key: "bullish",
        tone: "bullish",
        label: "偏多候选",
        confirmationPrice: levels.upper.price,
        priceMeaning: "条件确认价，不是直接成交价。",
        requirements: [{ label: "确认要求", detail: levels.upper.condition || "等待完整 K线与量能共同确认。" }],
        status: "awaiting_confirmation",
        statusLabel: "等待条件确认",
        statusDetail: "旧报告未附完整确认拆解；请结合当前图表刷新后阅读。",
        invalidation
      },
      {
        key: "bearish",
        tone: "bearish",
        label: "偏空候选",
        confirmationPrice: levels.lower.price,
        priceMeaning: "条件确认价，不是直接成交价。",
        requirements: [{ label: "确认要求", detail: levels.lower.condition || "等待完整 K线与量能共同确认。" }],
        status: "awaiting_confirmation",
        statusLabel: "等待条件确认",
        statusDetail: "旧报告未附完整确认拆解；请结合当前图表刷新后阅读。",
        invalidation
      }
    ]
  };
}

function marketAiScenarioBoard(outlook: MarketAiOutlookResponse | null, confirmationLevels: ReturnType<typeof marketAiConfirmationLevels>) {
  if (outlook?.scenarioBoard?.candidates?.length) return outlook.scenarioBoard;
  if (!confirmationLevels) return null;
  return {
    evidenceScore: outlook?.decision?.confidence ?? 0,
    scoreMeaning: "旧报告未附场景化决策数据；刷新后可查看规则化场景证据度。",
    marketState: {
      label: confirmationLevels.currentState.label,
      summary: confirmationLevels.currentState.summary,
      price: "--",
      rangeLow: outlook?.observationLevels?.neutralRange?.low ?? "--",
      rangeHigh: outlook?.observationLevels?.neutralRange?.high ?? "--",
      positionLabel: "区间位置待刷新"
    },
    dataLimitations: [{ label: "场景数据", detail: "旧报告未附完整场景拆解；刷新后可确认数据限制。" }],
    candidates: confirmationLevels.candidates.map((candidate) => ({
      key: candidate.key,
      label: candidate.label,
      tone: candidate.tone,
      status: "watch",
      statusLabel: candidate.statusLabel,
      confirmationPrice: candidate.confirmationPrice,
      priceCondition: candidate.requirements?.map((item) => item.detail).join("；") || "刷新后查看完整 K线条件。",
      distance: "--",
      distanceLabel: "距确认线",
      missingEvidence: candidate.missingEvidence,
      limitations: [],
      invalidation: candidate.invalidation
    }))
  };
}

function marketAiDirectionSummary(outlook: MarketAiOutlookResponse | null, scenarioBoard: ReturnType<typeof marketAiScenarioBoard>) {
  if (outlook?.directionSummary?.headline) return outlook.directionSummary;
  const candidates = scenarioBoard?.candidates ?? [];
  const clue = scenarioBoard?.marketState?.strongestClue;
  const clueText = `${clue?.label ?? ""} ${clue?.detail ?? ""}`;
  const preferred = clueText.includes("卖")
    ? candidates.find((item) => item.tone === "bearish")
    : clueText.includes("买")
      ? candidates.find((item) => item.tone === "bullish")
      : candidates[0];
  const limited = Boolean(scenarioBoard?.dataLimitations?.length);
  return {
    headline: limited ? "方向暂不可判定" : "无明确方向",
    state: limited ? "limited" : "watch",
    statusLabel: limited ? "缺关键数据" : "等待完整确认",
    direction: preferred?.tone === "bearish" ? "down" : preferred?.tone === "bullish" ? "up" : "neutral",
    tone: preferred?.tone === "bearish" ? "bearish" : preferred?.tone === "bullish" ? "bullish" : "neutral",
    reason: marketAiReadableText(clue?.detail) || marketAiReadableText(scenarioBoard?.marketState?.summary) || "旧报告未附方向优先摘要；当前不宜追向。",
    metLabel: "已满足",
    metCondition: marketAiReadableText(clue?.detail) || "旧报告未附完整方向线索。",
    missingLabel: limited ? "还差" : "等待",
    missingCondition: `${marketAiReadableText(preferred?.priceCondition) || "刷新后查看完整 K线条件。"}${limited ? "；交易结构数据不完整，价格条件达成后仍需等待数据恢复。" : ""}`,
    nextCondition: `${marketAiReadableText(preferred?.priceCondition) || "刷新后查看完整 K线条件。"}${limited ? "；交易结构数据不完整，价格条件达成后仍需等待数据恢复。" : ""}`,
    confirmationPrice: preferred?.confirmationPrice || "--",
    confirmationPriceLabel: limited ? "待验证价" : preferred?.tone === "bearish" ? "下方确认价" : "上方确认价",
    snapshot: scenarioBoard?.snapshot,
    readOnly: "基于当前行情快照的方向观察，不构成下单指令。"
  };
}

function marketAiMultiTimeframeTrend(outlook: MarketAiOutlookResponse | null) {
  const reported = outlook?.multiTimeframeTrend;
  const byKey = new Map((reported?.periods ?? []).flatMap((item) => (item?.key ? [[item.key, item]] : [])));
  const defaults = [
    { key: "15m", label: "15分钟" },
    { key: "1H", label: "1小时" },
    { key: "1D", label: "日线" },
  ];
  const periods = defaults.map((fallback) => {
    const item = byKey.get(fallback.key);
    if (item) return item;
    return {
      ...fallback,
      available: false,
      status: "unavailable",
      trend: "unavailable",
      trendLabel: "数据待刷新",
      evidence: [],
      condition: "刷新 AI 后读取该周期的真实 K线。",
      warning: "旧报告未包含此周期数据。",
    };
  });
  return {
    periods,
    alignment: marketAiReadableText(reported?.alignment) || "多周期数据待刷新；不会用其他周期替代。",
    alignmentState: reported?.alignmentState || "incomplete",
  };
}

function marketAiOverallView(outlook: MarketAiOutlookResponse | null) {
  return outlook?.overall?.view || marketAiStanceLabel(outlook?.stance);
}

function marketAiSummary(outlook: MarketAiOutlookResponse | null) {
  return outlook?.overall?.summary || outlook?.summary || "不会自动请求 AI，也不会改动交易单。点击右侧按钮后才开始分析。";
}

function marketAiChartSummary(outlook: MarketAiOutlookResponse | null) {
  const chartOnly = marketAiChartOnlyText(marketAiSummary(outlook));
  if (chartOnly) return chartOnly;
  const bar = outlook?.chartSnapshot?.bar || "当前";
  return `本次结论依据 ${bar} K线的价格、均线与量能快照生成，可结合下方图表依据核对。`;
}

function marketAiChartOnlyText(value?: string) {
  return marketAiReadableText(value)
    .split(/[；;。]/)
    .map((item) => item.trim())
    .filter((item) => item && !/\b(CPI|PPI|FOMC|Fed|BLS)\b|宏观|利率|外部数据|数据源/i.test(item))
    .join("；");
}

type MarketAiForecast = {
  key: string;
  label: string;
  direction: string;
  confidence: number;
  summary: string;
  condition: string;
};

function marketAiForecastDirection(value?: string) {
  if (value === "bullish" || value === "up") return "偏强推演";
  if (value === "bearish" || value === "down") return "偏弱推演";
  if (value === "neutral" || value === "range") return "区间推演";
  if (value === "wait") return "暂缓判断";
  return marketAiReadableText(value) || "等待图表确认";
}

function marketAiForecasts(outlook: MarketAiOutlookResponse | null): MarketAiForecast[] {
  const rowsByKey = new Map((outlook?.horizons ?? []).flatMap((item) => (item?.key ? [[item.key, item]] : [])));
  return ["15m", "1h", "today"].flatMap((key) => {
    const item = rowsByKey.get(key);
    if (!item) return [];
    const summary = marketAiChartOnlyText(item.summary);
    const condition = marketAiChartOnlyText(item.watch?.[0] || item.risk);
    if (!summary && !condition) return [];
    return [{
      key,
      label: marketAiHorizonLabel(key),
      direction: marketAiForecastDirection(item.bias),
      confidence: Math.max(0, Math.min(100, Number(item.confidence) || 0)),
      summary: summary || "当前图表变化后请手动刷新并重新阅读。",
      condition: condition || "当前图表变化后请手动刷新并重新阅读。"
    }];
  });
}

function marketAiSourceTitle(item: MarketAiSource) {
  const title = item.title || item.source || "数据来源";
  const freshness = item.cacheAgeMs === undefined || item.cacheAgeMs === null ? "" : ` · ${formatDuration(item.cacheAgeMs)}`;
  const date = item.publishedAt || item.scheduledAt;
  return `${title}${date ? ` · ${date}` : ""}${freshness}`;
}

function compactMarketAiWarnings(items?: string[]) {
  return Array.from(new Set((items ?? []).filter(Boolean))).slice(0, 4);
}

type MarketAiReadingFact = {
  label: string;
  value: string;
  detail?: string;
};

function marketAiTrendLabel(value?: string) {
  if (value === "up") return "短线偏强";
  if (value === "down") return "短线偏弱";
  if (value === "range") return "区间震荡";
  if (value === "volatile") return "波动加大";
  return value || "等待分析";
}

function marketAiReadableText(value?: string) {
  return (value ?? "")
    .replace(/recent20High/gi, "近20根最高价")
    .replace(/recent20Low/gi, "近20根最低价")
    .replace(/recent20RangePct/gi, "近20根振幅")
    .replace(/recentAverage/gi, "近期平均成交量")
    .replace(/previousAverage/gi, "前期平均成交量")
    .replace(/changePct/gi, "量能变化")
    .replace(/volume context/gi, "量能状态")
    .replace(/volumeRead/gi, "量能判断")
    .replace(/\btrend\s*[=:]/gi, "走势：")
    .replace(/contracting/gi, "缩量")
    .replace(/expanding/gi, "放量")
    .replace(/\bnormal\b/gi, "平稳")
    .replace(/\brange\b/gi, "区间震荡")
    .replace(/\bvolatile\b/gi, "波动加大")
    .replace(/\bup\b/gi, "偏强")
    .replace(/\bdown\b/gi, "偏弱")
    .replace(/\s+/g, " ")
    .trim();
}

function marketAiFactLabel(value: string) {
  if (/均线|\bMA\d+/i.test(value)) return "均线结构";
  if (/量能|成交量|平均成交量|缩量|放量/i.test(value)) return "量能变化";
  if (/区间|高点|低点|振幅/i.test(value)) return "价格区间";
  if (/涨跌|最新价|last/i.test(value)) return "价格位置";
  return "图表解读";
}

function marketAiPrice(value: string) {
  const numeric = Number(value.replace(/,/g, ""));
  return Number.isFinite(numeric) ? numeric.toLocaleString("zh-CN", { maximumFractionDigits: 4 }) : value;
}

function marketAiFactsFromText(value?: string): MarketAiReadingFact[] {
  const raw = value?.trim();
  if (!raw) return [];
  const facts: MarketAiReadingFact[] = [];
  const low = raw.match(/(?:recent20Low|近20根低点|近20根最低价)\s*[=:]?\s*([\d,.]+)/i)?.[1];
  const high = raw.match(/(?:recent20High|近20根高点|近20根最高价)\s*[=:]?\s*([\d,.]+)/i)?.[1];
  if (low && high) facts.push({ label: "近20根价格区间", value: `${marketAiPrice(low)} – ${marketAiPrice(high)}` });

  const ma = Array.from(raw.matchAll(/\b(MA(?:5|10|20|60))\s*[=(：:]?\s*([\d,.]+)/gi))
    .slice(0, 3)
    .map((item) => `${item[1].toUpperCase()} ${marketAiPrice(item[2])}`);
  if (ma.length) facts.push({ label: "均线位置", value: ma.join(" · ") });

  const recentAverage = raw.match(/recentAverage\s*[=:]?\s*([\d,.]+)/i)?.[1];
  const previousAverage = raw.match(/previousAverage\s*[=:]?\s*([\d,.]+)/i)?.[1];
  const volumeChange = raw.match(/(?:changePct|量能变化)\s*[=:约\s]*\s*([+-]?[\d,.]+%?)/i)?.[1];
  if (recentAverage || previousAverage || /contracting|expanding|缩量|放量/i.test(raw)) {
    const comparison = recentAverage && previousAverage ? `近期 ${marketAiPrice(recentAverage)}，前期 ${marketAiPrice(previousAverage)}` : undefined;
    facts.push({ label: "量能变化", value: /contracting|缩量/i.test(raw) ? "较前期缩量" : /expanding|放量/i.test(raw) ? "较前期放量" : "量能平稳", detail: volumeChange ? `较前期 ${volumeChange}` : comparison });
  }

  const amplitude = raw.match(/(?:recent20RangePct|近20根振幅)\s*[=:]?\s*([\d,.]+%?)/i)?.[1];
  if (amplitude) facts.push({ label: "近20根振幅", value: amplitude.endsWith("%") ? amplitude : `${amplitude}%` });

  if (!facts.length) {
    facts.push({ label: marketAiFactLabel(raw), value: marketAiReadableText(raw) });
  }
  return facts;
}

function marketAiPrimaryFacts(outlook: MarketAiOutlookResponse | null) {
  const structuralFact: MarketAiReadingFact[] = outlook?.technical?.trend
    ? [{ label: "当前结构", value: marketAiTrendLabel(outlook.technical.trend) }]
    : [];
  const candidates = [
    ...(outlook?.report?.keyFactors ?? []),
    ...(outlook?.technical?.notes ?? []),
    outlook?.technical?.volumeRead ?? "",
    ...(outlook?.technical?.keyLevels ?? [])
  ].filter((item) => !/\b(CPI|PPI|FOMC|Fed|BLS)\b/i.test(item));
  const unique = new Set<string>();
  return [...structuralFact, ...candidates.flatMap((item) => marketAiFactsFromText(item))]
    .filter((item) => {
      const key = `${item.label}:${item.value}:${item.detail ?? ""}`;
      if (unique.has(key)) return false;
      unique.add(key);
      return true;
    })
    .slice(0, 3);
}

function marketAiSupplementaryWarning(value: string) {
  const readable = marketAiReadableText(value)
    .replace(/BLS CPI/gi, "美国 CPI")
    .replace(/Federal Reserve/gi, "美联储")
    .replace(/incomplete response/gi, "返回不完整")
    .replace(/failed to fetch/gi, "暂时无法获取");
  return readable.length > 110 ? `${readable.slice(0, 110)}…` : readable;
}

function useMarketStats(selected: string, requestedStatsPeriod: string) {
  const [marketStats, setMarketStats] = React.useState<MarketStatsResponse | null>(null);
  const [marketStatsLoading, setMarketStatsLoading] = React.useState(false);
  const [marketStatsWarning, setMarketStatsWarning] = React.useState("");
  const [reloadNonce, setReloadNonce] = React.useState(0);
  const forceReloadRef = React.useRef(false);
  const effectiveStatsPeriod = effectiveMarketStatsPeriod(requestedStatsPeriod);
  const displayedMarketStats = marketStats?.instId === selected ? marketStats : null;
  const displayedStatsPeriod = displayedMarketStats?.period ?? effectiveStatsPeriod;
  const statsPeriodMismatch = requestedStatsPeriod !== displayedStatsPeriod;
  const longShortStats = displayedMarketStats?.longShortAccountRatio;
  const takerVolumeStats = displayedMarketStats?.takerVolume;
  const openInterestStats = displayedMarketStats?.openInterest;
  const statsWarnings = [...(displayedMarketStats?.warnings ?? []), marketStatsWarning].filter(Boolean);
  const statsUpdatedAt = displayedMarketStats?.ts ? new Date(displayedMarketStats.ts).toLocaleTimeString("zh-CN") : "--";

  const reload = React.useCallback((options?: { force?: boolean }) => {
    forceReloadRef.current = Boolean(options?.force);
    setReloadNonce((value) => value + 1);
  }, []);

  React.useEffect(() => {
    if (!selected) {
      setMarketStatsWarning("");
      setMarketStatsLoading(false);
      return;
    }
    let active = true;
    const force = forceReloadRef.current;
    forceReloadRef.current = false;
    setMarketStatsWarning("");
    setMarketStatsLoading(true);
    const params = new URLSearchParams({ instId: selected, period: requestedStatsPeriod, limit: "100" });
    if (force) params.set("force", "true");
    fetch(`${API_BASE}/api/market/stats?${params.toString()}`)
      .then(async (response) => {
        if (!response.ok) throw new Error("交易统计加载失败");
        return response.json();
      })
      .then((payload: MarketStatsResponse) => {
        if (!active) return;
        setMarketStats(payload);
        setMarketStatsWarning("");
      })
      .catch((error) => {
        if (!active) return;
        setMarketStatsWarning(error instanceof Error ? error.message : "交易统计加载失败");
      })
      .finally(() => {
        if (active) setMarketStatsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadNonce, requestedStatsPeriod, selected]);

  return {
    marketStats: displayedMarketStats,
    marketStatsLoading,
    requestedStatsPeriod,
    effectiveStatsPeriod,
    displayedStatsPeriod,
    statsPeriodMismatch,
    longShortStats,
    takerVolumeStats,
    openInterestStats,
    statsWarnings,
    statsUpdatedAt,
    reload
  };
}

type MarketStatsModel = ReturnType<typeof useMarketStats>;

function TradingStatsSummary({
  selected,
  stats,
  action,
  compact = false
}: {
  selected: string;
  stats: MarketStatsModel;
  action?: React.ReactNode;
  compact?: boolean;
}) {
  const uniqueWarnings = Array.from(new Set(stats.statsWarnings));
  const initialStatsLoading = stats.marketStatsLoading && !stats.marketStats;

  return (
    <Paper component="section" className={`tradingStatsPanel ${compact ? "compact" : ""}`} aria-label="合约交易结构">
      <div className="tradingStatsHeader">
        <div>
          <strong>交易结构</strong>
          <span>
            {selected} · 统计 {stats.displayedStatsPeriod}
            {stats.statsPeriodMismatch ? ` · K线 ${stats.requestedStatsPeriod}` : ""}
          </span>
        </div>
        <div className="tradingStatsHeaderActions">
          <Badge
            className={`statusPill ${uniqueWarnings.length ? "warning" : "live"}`}
            title={uniqueWarnings.map((item) => marketStatsWarningLabel(item)).join("；")}
            color={uniqueWarnings.length ? "yellow" : "teal"}
            variant="light"
          >
            {stats.marketStatsLoading ? (initialStatsLoading ? "统计加载中" : "统计更新中") : uniqueWarnings.length ? "统计部分回退" : sourceLabel(stats.marketStats?.source)}
          </Badge>
          <Button
            type="button"
            className="secondaryButton slim tradingStatsRetry"
            onClick={() => stats.reload({ force: true })}
            disabled={stats.marketStatsLoading}
            title="重新加载交易统计"
            variant="default"
            size="xs"
            leftSection={<RefreshCw size={15} />}
          >
            {stats.marketStatsLoading ? "刷新中" : "重新加载"}
          </Button>
          {action}
        </div>
      </div>
      {initialStatsLoading ? <DataLoadingSkeleton variant="metrics" label="正在读取合约交易统计" /> : <div className="tradingStatsGrid">
        <Metric
          label="合约多空人数比"
          value={stats.marketStatsLoading ? "加载中" : formatValue(stats.longShortStats?.latest)}
          valueClass={marketStatsRatioClass(stats.longShortStats?.latest)}
        />
        <Metric
          label="多空账户状态"
          value={stats.marketStatsLoading ? "加载中" : longShortBiasLabel(stats.longShortStats?.bias)}
        />
        <Metric
          label="主动买入占比"
          value={stats.marketStatsLoading ? "加载中" : formatStatsPercentPoint(stats.takerVolumeStats?.buySharePct)}
          valueClass={marketStatsBuyShareClass(stats.takerVolumeStats?.buySharePct)}
        />
        <Metric
          label="主动买卖状态"
          value={stats.marketStatsLoading ? "加载中" : takerDominanceLabel(stats.takerVolumeStats?.dominance)}
        />
        <Metric
          label="持仓量 USD"
          value={stats.marketStatsLoading ? "加载中" : formatStatsCompact(stats.openInterestStats?.oiUsd, "USD")}
        />
        <Metric
          label="持仓变化"
          value={stats.marketStatsLoading ? "加载中" : formatStatsPercentPoint(stats.openInterestStats?.changePct)}
          valueClass={marketStatsSignedClass(stats.openInterestStats?.changePct)}
        />
      </div>}
      {!compact ? (
        <div className="tradingStatsNarrative">
          <span>{longShortBiasLabel(stats.longShortStats?.bias)}</span>
          <span>{takerDominanceLabel(stats.takerVolumeStats?.dominance)}</span>
          <span>{openInterestTrendLabel(stats.openInterestStats?.trend)}</span>
          {stats.statsPeriodMismatch ? (
            <span>
              统计周期 {stats.displayedStatsPeriod}，不同于当前 K线 {stats.requestedStatsPeriod}
            </span>
          ) : null}
          <span>更新 {stats.statsUpdatedAt}</span>
        </div>
      ) : null}
      {!compact && uniqueWarnings.length ? (
        <div className="tradingStatsWarnings">
          {uniqueWarnings.map((item) => (
            <span key={item}>{marketStatsWarningLabel(item)}</span>
          ))}
        </div>
      ) : null}
    </Paper>
  );
}

function TradingStatsDetails({ stats }: { stats: MarketStatsModel }) {
  return (
    <section className="tradingStatsDetails" aria-label="交易统计明细">
      <Paper className="tradingStatsDetail">
        <div className="tradingStatsDetailHeader">
          <strong>多空人数比</strong>
          <span>{longShortBiasLabel(stats.longShortStats?.bias)}</span>
        </div>
        <div className="statPointList">
          {recentMarketStatsPoints(stats.longShortStats?.points, 8).length ? (
            recentMarketStatsPoints(stats.longShortStats?.points, 8).map((point) => (
              <span key={point.ts}>
                {formatPointTime(point.ts)} <strong>{formatValue(point.ratio)}</strong>
              </span>
            ))
          ) : (
            <span>暂无多空人数比数据</span>
          )}
        </div>
      </Paper>
      <Paper className="tradingStatsDetail">
        <div className="tradingStatsDetailHeader">
          <strong>主动买卖</strong>
          <span>{takerDominanceLabel(stats.takerVolumeStats?.dominance)}</span>
        </div>
        <div className="statPointList">
          {recentMarketStatsPoints(stats.takerVolumeStats?.points, 8).length ? (
            recentMarketStatsPoints(stats.takerVolumeStats?.points, 8).map((point) => (
              <span key={point.ts}>
                {formatPointTime(point.ts)} 买 {formatStatsCompact(point.buyVol)} / 卖 {formatStatsCompact(point.sellVol)}
              </span>
            ))
          ) : (
            <span>暂无主动买卖数据</span>
          )}
        </div>
      </Paper>
      <Paper className="tradingStatsDetail">
        <div className="tradingStatsDetailHeader">
          <strong>持仓量</strong>
          <span>{openInterestTrendLabel(stats.openInterestStats?.trend)}</span>
        </div>
        <div className="statPointList">
          {recentMarketStatsPoints(stats.openInterestStats?.points, 8).length ? (
            recentMarketStatsPoints(stats.openInterestStats?.points, 8).map((point) => (
              <span key={point.ts}>
                {formatPointTime(point.ts)} <strong>{formatStatsCompact(point.oiUsd || point.oiCcy || point.oi)}</strong>
              </span>
            ))
          ) : (
            <span>暂无持仓量数据</span>
          )}
        </div>
      </Paper>
    </section>
  );
}

function Disclosure({ className, label, children }: { className: string; label: React.ReactNode; children: React.ReactNode }) {
  const [opened, setOpened] = React.useState(false);
  const contentId = React.useId();
  return (
    <div className={className} data-expanded={opened || undefined}>
      <UnstyledButton
        type="button"
        className="disclosureTrigger"
        aria-expanded={opened}
        aria-controls={contentId}
        onClick={() => setOpened((value) => !value)}
      >
        {label}
      </UnstyledButton>
      <Collapse expanded={opened}>
        <div id={contentId} className="disclosureBody">{children}</div>
      </Collapse>
    </div>
  );
}

function MarketAiVerificationPanel({ selected, reportGeneratedAt, reportPlan }: { selected: string; reportGeneratedAt?: number; reportPlan?: MarketAiOutlookResponse["pricePlan"] }) {
  const [history, setHistory] = React.useState<MarketAiVerificationHistory | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [opened, setOpened] = React.useState(false);
  const detailsId = React.useId();

  React.useEffect(() => {
    let active = true;
    const readHistory = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/market/ai-outlook/evaluations?instId=${encodeURIComponent(selected)}&limit=12`);
        if (!response.ok) throw new Error("verification history unavailable");
        const payload = (await response.json()) as MarketAiVerificationHistory;
        if (active) {
          setHistory(payload);
          setError(false);
        }
      } catch {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    };
    setLoading(true);
    void readHistory();
    const interval = window.setInterval(() => void readHistory(), 60_000);
    return () => { active = false; window.clearInterval(interval); };
  }, [selected, reportGeneratedAt]);

  const current = history?.instId === selected ? history : null;
  const labels: Record<string, string> = {
    pending: "待验证", hit: "方向符合", miss: "方向未符", flat: "波动不足",
    not_scored: "不计分", insufficient_data: "数据不足"
  };
  const directionLabel = (direction: string) => direction === "long" ? "看涨" : direction === "short" ? "看跌" : "无方向";
  const kindLabel = (kind: string) => kind === "price_plan_15m" ? "15分钟价格计划" : "主图方向";
  const unscoredLabel = (sample: MarketAiVerificationHistory["samples"][number]) => {
    if (sample.unscoredReason && !sample.unscoredReason.startsWith("无可核验方向")) return sample.unscoredReason;
    if (sample.direction === "none") return "本次没有明确方向";
    if (sample.kind === "price_plan_15m" && sample.planStatus !== "ready" && sample.planStatus !== "watch") return "价格计划未处于有效观察状态";
    return "未纳入方向比例";
  };
  const stats = [
    ["main_direction", "主图方向"],
    ["price_plan_15m", "15分钟价格计划"]
  ] as const;
  const latestPlan = current?.samples.find((sample) => sample.kind === "price_plan_15m" && (!reportGeneratedAt || Math.abs(sample.createdAt - reportGeneratedAt) < 1000))
    ?? (reportGeneratedAt && reportPlan?.entryPrice ? current?.samples.find((sample) => sample.kind === "price_plan_15m" && sample.createdAt <= reportGeneratedAt
      && sample.planValidUntil === reportPlan.validUntil && sample.direction === reportPlan.direction
      && sample.entryPrice === String(reportPlan.entryPrice) && sample.targetPrice === String(reportPlan.targetPrice) && sample.stopPrice === String(reportPlan.stopPrice)) : undefined);
  const latestPlanHasPrices = Boolean(latestPlan?.entryPrice && (latestPlan.direction === "long" || latestPlan.direction === "short"));
  const latestPlanReturn = marketAiHypotheticalReturn(latestPlan?.hypotheticalCloseReturnPct);
  const latestPlanEntryState = latestPlan ? marketAiPlanEntryState(latestPlan) : null;
  const reusedPlanSample = Boolean(latestPlan && reportGeneratedAt && Math.abs(latestPlan.createdAt - reportGeneratedAt) >= 1000);
  const summary = !current
    ? loading ? "正在读取核验记录" : error ? "核验记录暂时无法读取" : "暂无核验记录"
    : latestPlan
      ? latestPlanHasPrices ? `${reusedPlanSample ? "同一计划样本" : reportGeneratedAt ? "本次计划" : "最近计划"}：${latestPlanEntryState?.label || "待核验"}` : `${reportGeneratedAt ? "本次" : "最近"}未生成可核验买卖计划`
      : reportGeneratedAt ? "本次报告暂无可显示的价格计划核验记录" : current.samples.length ? `已有 ${current.samples.length} 条预测样本` : "暂无预测样本，开始分析后自动保存";

  return (
    <section className="marketAiVerification" aria-label="AI预测事后核验" data-expanded={opened || undefined}>
      <div className="marketAiVerificationHeader">
        <div>
          <span className="marketAiSectionLabel">预测事后核验</span>
          <strong>{summary}</strong>
          <small>{error && current ? "记录更新失败，当前显示上次结果。" : "新计划冻结分析时买一／卖一报价，收盘后用完整 1 分钟 K 线核对止盈价；报价和到价均不代表成交。"}</small>
        </div>
        <div className="marketAiVerificationActions">
          {loading && current ? <span role="status">更新中</span> : null}
          <Button type="button" variant="default" size="xs" aria-expanded={opened} aria-controls={detailsId} onClick={() => setOpened((value) => !value)}>
            {opened ? "收起记录" : "查看记录"}
          </Button>
        </div>
      </div>
      {latestPlanHasPrices && latestPlan ? <div className="marketAiVerificationHeadline" aria-label="本次计划核验摘要" aria-live="polite">
        <div><span>{reusedPlanSample ? "样本首次记录" : "预测生成"}</span><strong>{new Date(latestPlan.createdAt).toLocaleString("zh-CN")}</strong></div>
        <div><span>{latestPlan.entryBasis === "quote_snapshot" ? "入场报价" : "入场核验"}</span><strong className={`marketAiVerificationStatus ${latestPlanEntryState?.tone || ""}`}>{latestPlanEntryState?.label || "待核验"}</strong><small>行情方向：{labels[latestPlan.status] || "待核验"}</small></div>
        <div><span>{latestPlan.entryBasis === "quote_snapshot" ? latestPlan.direction === "short" ? "分析时买一价 · 预计卖出" : "分析时卖一价 · 预计买入" : latestPlan.direction === "short" ? "旧计划预计卖出价" : "旧计划预计买入价"}</span><strong>{latestPlan.entryPrice || "未给出"}</strong><small>{latestPlan.entryBasis === "quote_snapshot" && latestPlan.entryQuoteTs ? `报价时间 ${new Date(latestPlan.entryQuoteTs).toLocaleString("zh-CN")}` : latestPlanEntryState?.label}</small></div>
        <div><span>预测止盈价</span><strong>{latestPlan.targetPrice || "未给出"}</strong><small>{marketAiPlannedTargetMove(latestPlan.entryPrice, latestPlan.targetPrice, latestPlan.direction)} · {marketAiTargetState(latestPlan)}{latestPlan.targetObservedAt ? ` · 首次到价分钟 ${new Date(latestPlan.targetObservedAt).toLocaleString("zh-CN")}` : ""}</small></div>
        <div><span>核验收盘 / 时间</span><strong>{latestPlan.observedClose || (latestPlan.status === "pending" ? "等待收盘" : "未取得")}</strong><small>{latestPlan.evaluatedAt ? new Date(latestPlan.evaluatedAt).toLocaleString("zh-CN") : `预计 ${new Date(latestPlan.dueAt).toLocaleString("zh-CN")} 后`}</small></div>
        <div className={`marketAiVerificationReturn ${latestPlan.status === "pending" ? "pending" : "unconfirmed"}`}><span>交易收益率</span><strong>{latestPlan.status === "pending" ? "待核验" : marketAiEntryNotObserved(latestPlan) ? "未观察到入场 · 不适用" : "成交未证实 · 不适用"}</strong>{latestPlanReturn ? <b className={`marketAiPriceComparison ${latestPlanReturn.tone}`}>{latestPlanReturn.label} · 仅作价格对照</b> : null}<small>{latestPlan.status === "pending" ? "收盘后更新" : "未记录实际成交"}</small></div>
      </div> : null}
      {latestPlanHasPrices && latestPlan ? <small className="marketAiVerificationBoundary">{reusedPlanSample ? "本次报告沿用相同计划的首次样本，不重复计数。" : ""}{marketAiTargetSequence(latestPlan)}{marketAiHypotheticalReturnNote(latestPlan)}行情方向只比较基准 K 线与目标收盘，不判断是否入场。</small> : latestPlan ? <small className="marketAiVerificationBoundary">预测生成 {new Date(latestPlan.createdAt).toLocaleString("zh-CN")} · 未给出买卖价，不计入价格计划方向核验。</small> : null}
      <Collapse expanded={opened}>
        <div id={detailsId} className="marketAiVerificationDetails">
          {loading && !current ? <DataLoadingState label="正在读取历史核验记录" compact /> : null}
          {error ? <p className="marketAiVerificationMessage" role="status">核验记录暂时无法更新，稍后会自动重试。{current ? "下方保留上次记录。" : ""}</p> : null}
          {current ? <>
            <div className="marketAiVerificationStats">
              {stats.map(([kind, label]) => {
                const item = current.summary[kind];
                if (!item) return null;
                return <div key={kind}>
                  <span>{label}</span>
                  <strong>{item.hitRatePct === null ? "样本积累中" : `${item.hitRatePct}% 方向符合`}</strong>
                  <small>符合 {item.hit} / 不符 {item.miss} · 已计分 {item.scored} 次{item.pending ? ` · 待验证 ${item.pending}` : ""}{item.not_scored ? ` · 不计分 ${item.not_scored}` : ""}</small>
                  {item.hitRatePct === null ? <small>至少 {item.minimumRateSamples} 次有效核验后显示比例</small> : null}
                </div>;
              })}
            </div>
            {current.samples.length ? <div className="marketAiVerificationList" aria-label="最近核验样本">
              {current.samples.slice(0, 6).map((sample) => <div className="marketAiVerificationRow" key={sample.id}>
                <div>
                  <b>{kindLabel(sample.kind)} · {sample.bar} · {directionLabel(sample.direction)}</b>
                  <small>{new Date(sample.createdAt).toLocaleString("zh-CN")} 生成</small>
                </div>
                <span className={`marketAiVerificationStatus ${sample.status}`}>{labels[sample.status] || "待核验"}</span>
                <small>{sample.status === "pending" ? `预计 ${new Date(sample.dueAt).toLocaleString("zh-CN")} 后核验` : sample.observedClose ? `基准 ${sample.baselineClose} → 收盘 ${sample.observedClose}` : unscoredLabel(sample)}</small>
                {sample.kind === "price_plan_15m" && sample.entryReferenceTouched !== null && sample.entryReferenceTouched !== undefined ? <small className="marketAiVerificationPriceObservation">下一根 K 线区间{sample.entryReferenceTouched ? "触及" : "未触及"}{sample.direction === "short" ? "卖出" : "买入"}参考价；不代表成交。</small> : null}
              </div>)}
            </div> : <p className="marketAiVerificationMessage">当前合约暂无预测样本。开始一次新分析后，会自动保存并等待下一根完整 K 线。</p>}
            <small className="marketAiVerificationScope">{current.scope} “方向符合比例”仅计算符合和不符；波动不足、数据不足及不计分样本不计入。</small>
          </> : null}
        </div>
      </Collapse>
    </section>
  );
}

function MarketAiOutlookPanel({
  selected,
  outlook,
  chartSnapshot,
  chartHasNewerSnapshot,
  loading,
  analysisAvailable,
  snapshotLoading,
  error,
  onRefresh,
  fullPage = false
}: {
  selected: string;
  outlook: MarketAiOutlookResponse | null;
  chartSnapshot: ChartSnapshotMetadata | null;
  chartHasNewerSnapshot: boolean;
  loading: boolean;
  analysisAvailable: boolean;
  snapshotLoading: boolean;
  error: string;
  onRefresh: () => void;
  fullPage?: boolean;
}) {
  const [planNow, setPlanNow] = React.useState(() => Date.now());
  React.useEffect(() => {
    const interval = window.setInterval(() => setPlanNow(Date.now()), 10_000);
    return () => window.clearInterval(interval);
  }, []);
  const initialAnalysisLoading = loading && !outlook;
  const refreshingAnalysis = loading && Boolean(outlook);
  const warnings = compactMarketAiWarnings(outlook?.warnings);
  const riskNotes = [...(outlook?.report?.riskNotes ?? []), ...(outlook?.suggestion?.riskNotes ?? [])];
  const sourceItems = (outlook?.sources ?? []).slice(0, 5);
  const analysisProfile = outlook?.analysisProfile?.status === "active" ? outlook.analysisProfile : null;
  const primaryFacts = marketAiPrimaryFacts(outlook);
  const forecasts = marketAiForecasts(outlook);
  const decision = outlook?.decision;
  const confidenceExplanation = marketAiConfidenceExplanation(outlook);
  const evidenceGaps = marketAiEvidenceGaps(outlook);
  const periodProvenance = marketAiPeriodProvenance(outlook);
  const tradingStructure = outlook?.tradingStructure;
  const structureItems = tradingStructure?.items ?? [];
  const observationLevels = outlook?.observationLevels;
  const confirmationLevels = marketAiConfirmationLevels(observationLevels);
  const scenarioBoard = marketAiScenarioBoard(outlook, confirmationLevels);
  const directionSummary = marketAiDirectionSummary(outlook, scenarioBoard);
  const pricePlan = outlook?.pricePlan;
  const pricePlanExpired = Boolean(pricePlan?.status !== "unavailable" && pricePlan?.validUntil && planNow >= pricePlan.validUntil);
  const pricePlanQuoteExpired = Boolean(pricePlan?.status === "ready" && pricePlan?.quoteTs && planNow - pricePlan.quoteTs > 30_000);
  const pricePlanStatus = pricePlanExpired ? "expired" : pricePlanQuoteExpired ? "watch" : pricePlan?.status || "unavailable";
  const pricePlanWaitingForClose = pricePlanStatus === "watch" && pricePlan?.entryBasis !== "quote_snapshot" && pricePlan?.priceConditionMet === false;
  const pricePlanTitle = pricePlan?.direction === "long" ? pricePlanStatus === "watch" && pricePlan.entryBasis !== "quote_snapshot" ? "做多候选条件" : "做多价格计划" : pricePlan?.direction === "short" ? pricePlanStatus === "watch" && pricePlan.entryBasis !== "quote_snapshot" ? "做空候选条件" : "做空价格计划" : "暂无合格交易计划";
  const pricePlanStatusLabel = pricePlanStatus === "watch" ? pricePlanWaitingForClose ? "等待完整 K 线收盘" : pricePlanQuoteExpired ? "报价已过时" : pricePlan?.entryBasis === "quote_snapshot" ? "价差偏宽 · 仅供参考" : "报价与入场条件待复核" : ({ ready: pricePlan?.entryBasis === "quote_snapshot" ? "分析时报价已记录" : "上根收盘条件已满足", missed: "已过价，需重算", expired: "计划已过期", no_plan: "多空证据未分出主方向", unavailable: "数据待补齐" } as Record<string, string>)[pricePlanStatus] || "数据待补齐";
  const multiTimeframeTrend = marketAiMultiTimeframeTrend(outlook);
  const scenarioEvidenceScore = scenarioBoard?.evidenceScore ?? decision?.confidence ?? marketAiConfidence(outlook);
  const analysisScopeState = loading
    ? "读取中"
    : outlook
      ? "本次报告已生成"
      : snapshotLoading
        ? "图表准备中"
        : "待分析";
  const analysisScopeDescription = loading
    ? "正在一次性读取 15分钟、1小时和日线的独立 K线快照。"
    : outlook
      ? "下方展示本次报告中各周期的真实结果与数据状态。"
      : snapshotLoading
        ? "图表快照就绪后，开始一次分析即可自动读取三个固定周期。"
        : "开始一次分析后，系统会自动读取三个固定周期；无需分别点击。";
  const observationLevelState = chartHasNewerSnapshot
    ? "图表已有新数据 · 手动刷新后重算确认价"
    : observationLevels?.partialConfirmation
      ? "交易结构部分可用 · 确认条件不完整"
      : `基于本次 ${observationLevels?.bar || "当前"} K线快照`;
  const focusItems = outlook?.report?.focus?.length
    ? outlook.report.focus
    : [outlook?.suggestion?.condition || "等待报告生成后查看可关注的市场变化。"];
  const reassessItems = outlook?.report?.reassess?.length
    ? outlook.report.reassess
    : [outlook?.suggestion?.invalidation || "宏观事件或K线结构变化后需要重新阅读。"];
  const reportSnapshot = outlook?.chartSnapshot ?? chartSnapshot;
  const dataStatus = reportSnapshot
    ? `${reportSnapshot.bar} · ${reportSnapshot.candleCount} 根K线 · ${new Date(reportSnapshot.lastCandleTs || reportSnapshot.snapshotTs).toLocaleTimeString("zh-CN")} · ${sourceLabel(reportSnapshot.source)}`
    : "正在初始化当前图表快照";
  const snapshotState = !reportSnapshot
    ? "图表快照加载中"
    : !reportSnapshot.complete
      ? "图表数据待确认"
      : reportSnapshot.warning
        ? "图表数据有提示"
        : "图表数据完整";
  const supplementaryItems = Array.from(new Set([...warnings, ...riskNotes])).map(marketAiSupplementaryWarning);
  const externalSourceWarning = supplementaryItems.length > 0;

  return (
    <Paper component="section" className={`marketAiOutlookPanel ${outlook ? "ready" : ""} ${fullPage ? "fullPage" : ""}`} aria-label="AI看行情">
      <div className="marketAiHeader">
        <div>
          <span className="eyebrow">AI看行情</span>
          <strong>{outlook ? (pricePlan ? pricePlanTitle : marketAiReadableText(directionSummary?.headline) || marketAiOverallView(outlook)) : `${selected} 主图观察待分析`}</strong>
          <small>
            {outlook
              ? `${sourceLabel(outlook.source)}${outlook.cached ? " · 已缓存" : ""} · 场景证据度 ${scenarioEvidenceScore}%`
              : "手动触发后解读主图快照，并自动读取固定三周期；方向推演仅供参考"}
          </small>
        </div>
        <Button type="button" className="secondaryButton slim" onClick={onRefresh} disabled={loading || !analysisAvailable} aria-busy={loading} title={analysisAvailable ? "刷新AI看行情" : "正在读取图表快照，完成后可开始分析"} variant="default" size="xs" leftSection={<BrainCircuit size={15} className={loading ? "marketAiRefreshIcon isSpinning" : "marketAiRefreshIcon"} />}>
          {loading ? "分析中" : !analysisAvailable ? "图表准备中" : outlook ? "刷新AI" : "开始分析"}
        </Button>
      </div>

      {snapshotLoading && !reportSnapshot ? <DataLoadingState label="正在读取当前图表快照，完成后即可开始分析" /> : null}

      {loading ? (
        <div className={`marketAiLoadingState ${refreshingAnalysis ? "refreshing" : "initial"}`} role="status" aria-live="polite">
          <span className="marketAiLoadingSpinner" aria-hidden="true" />
          <span>{refreshingAnalysis ? "正在更新行情快照与 15分钟、1小时、日线趋势 · 当前仍显示上一份报告" : "正在一次性读取 15分钟、1小时和日线的独立 K线快照…"}</span>
        </div>
      ) : null}

      {error ? <Notice tone="danger">{error}</Notice> : null}

      {outlook ? (
        <section className={`marketAiPricePlan ${pricePlan?.direction || "none"} ${pricePlanStatus}`} aria-label="15分钟买卖价格计划">
          <div className="marketAiPricePlanHeader">
            <div>
              <span className="marketAiSectionLabel">{pricePlanStatus === "watch" && pricePlan?.entryBasis !== "quote_snapshot" ? "15分钟候选条件 · 只读观察" : "15分钟交易计划 · 只读参考"}</span>
              <strong>{pricePlan ? pricePlanTitle : "价格计划待更新"}</strong>
              <small className="marketAiPricePlanGenerated">预测生成：{outlook.generatedAt ? new Date(outlook.generatedAt).toLocaleString("zh-CN") : "未记录"}</small>
            </div>
            <span className="marketAiPricePlanStatus">{pricePlan ? pricePlanStatusLabel : "旧报告待刷新"}</span>
          </div>
          {pricePlan ? (
            <>
              {pricePlan.entryPrice && pricePlan.stopPrice && pricePlan.targetPrice ? (
                <>
                  <div className="marketAiPricePlanWindow" aria-label="入场观察期">
                    <div><span>{pricePlan.entryBasis === "quote_snapshot" ? "报价记录时间" : pricePlanStatus === "watch" ? "条件观察开始" : "入场观察开始"}</span><strong>{pricePlan.entryBasis === "quote_snapshot" && pricePlan.entryQuoteTs ? new Date(pricePlan.entryQuoteTs).toLocaleString("zh-CN") : outlook.generatedAt ? new Date(outlook.generatedAt).toLocaleString("zh-CN") : "未记录"}</strong></div>
                    <span className="marketAiPricePlanWindowArrow" aria-hidden="true">→</span>
                    <div><span>{pricePlanStatus === "watch" && pricePlan.entryBasis !== "quote_snapshot" ? "本轮条件复核" : "目标核验截止"}</span><strong>{pricePlan.validUntil ? new Date(pricePlan.validUntil).toLocaleString("zh-CN") : "未记录"}</strong></div>
                  </div>
                  {pricePlanStatus === "watch" ? <p className="marketAiPricePlanWatchNote">{marketAiWatchConditionNote(pricePlan.priceConditionMet, pricePlan.entryBasis)}</p> : null}
                  <div className="marketAiPricePlanPrices">
                    <div className="marketAiPricePlanEntry"><span>{pricePlan.entryBasis === "quote_snapshot" ? pricePlan.direction === "long" ? "分析时卖一价 · 预计做多买入" : "分析时买一价 · 预计做空卖出" : `${pricePlanStatus === "watch" ? "候选价" : "入场参考"} · ${pricePlan.direction === "long" ? "做多买入" : "做空卖出"}`}</span><strong>{formatValue(pricePlan.entryPrice)}</strong><small>{pricePlan.entryBasis === "quote_snapshot" && pricePlan.entryQuoteTs ? `报价时间 ${new Date(pricePlan.entryQuoteTs).toLocaleString("zh-CN")} · 未证实成交` : pricePlanStatus === "watch" ? marketAiWatchEntryLabel(pricePlan.priceConditionMet, pricePlan.entryBasis) : pricePlanExpired ? "历史参考价 · 已过期" : "仅在观察期内按条件参考"}</small></div>
                    <div><span>若已入场 · 止盈{pricePlan.direction === "long" ? "卖出平多" : "买回平空"}</span><strong>{formatValue(pricePlan.targetPrice)}</strong><small>{marketAiPlannedTargetMove(pricePlan.entryPrice, pricePlan.targetPrice, pricePlan.direction)} · 未入场时不生效</small></div>
                    <div><span>若已入场 · 止损{pricePlan.direction === "long" ? "卖出平多" : "买回平空"}</span><strong>{formatValue(pricePlan.stopPrice)}</strong><small>未入场时不生效</small></div>
                  </div>
                  <p className="marketAiPricePlanExit">{pricePlan.entryBasis === "quote_snapshot" ? "预计入场价是分析时看到的报价，不是已成交价格。后续只验证止盈目标是否到价，不推断实际买卖或盈利。" : "只有确认入场后，止盈和止损价才有意义；二者是不同的退出情形，不能据此推断实际成交时间或价格。"}</p>
                  {pricePlan.priceLogic ? <MarketAiPriceLogicDetails logic={pricePlan.priceLogic} /> : <p className="marketAiPricePlanLogicMissing">这份较早的报告未保存完整计算明细；刷新分析后可查看对应数值与公式。</p>}
                </>
              ) : null}
              <p className="marketAiPricePlanReason">{pricePlanExpired ? "计划已到有效期限，请刷新分析后重新核对价格。" : pricePlanQuoteExpired ? "报价已超过30秒，请刷新分析后重新核对价格。" : marketAiReadableText(pricePlan.reason)}</p>
              {pricePlan.upperReassess && pricePlan.lowerReassess ? (
                <p className="marketAiPricePlanAlternatives">重新评估：上方 {formatValue(pricePlan.upperReassess)} · 下方 {formatValue(pricePlan.lowerReassess)}</p>
              ) : null}
              {pricePlan.condition ? <p className="marketAiPricePlanCondition"><b>生效条件</b>{marketAiReadableText(pricePlan.condition)}</p> : null}
              {pricePlan.validUntil ? <p className="marketAiPricePlanValidity">基于 {pricePlan.bar || "15m"} 已收盘 K线 · 有效至 {new Date(pricePlan.validUntil).toLocaleString("zh-CN")}</p> : null}
              {pricePlan.evidence?.length ? <p className="marketAiPricePlanEvidence">依据：{pricePlan.evidence.slice(0, 4).map(marketAiReadableText).join("；")}</p> : null}
              <small>{marketAiReadableText(pricePlan.priceMeaning)} {marketAiReadableText(pricePlan.costNote)}</small>
            </>
          ) : <p className="marketAiPricePlanReason">这份缓存报告没有价格计划。点击“刷新AI”生成新的 15分钟计划。</p>}
        </section>
      ) : null}

      <MarketAiVerificationPanel selected={selected} reportGeneratedAt={outlook?.generatedAt} reportPlan={outlook?.pricePlan} />

      <section className={`marketAiAnalysisScope ${loading ? "loading" : outlook ? "complete" : "pending"}`} aria-label="一次分析范围">
        <div className="marketAiAnalysisScopeHeader">
          <div>
            <span className="marketAiSectionLabel">一次分析范围</span>
            <strong>自动读取三个独立周期</strong>
            <small>{analysisScopeDescription}</small>
          </div>
          <span className="marketAiAnalysisScopeState">{analysisScopeState}</span>
        </div>
        <div className="marketAiAnalysisScopePeriods" aria-label="固定分析周期">
          {["15分钟", "1小时", "日线"].map((period) => (
            <span key={period}>
              <b>{period}</b>
              <small>{loading ? "读取中" : outlook ? "结果见下方" : "本次自动读取"}</small>
            </span>
          ))}
        </div>
      </section>

      {outlook && decision && scenarioBoard ? (
        <section className="marketAiScenarioBoard" aria-label="场景化决策看板">
          {!(reportSnapshot?.bar === "15m" && pricePlan?.entryPrice) ? <section className={`marketAiDirectionSummary ${directionSummary?.tone ?? "neutral"} ${directionSummary?.state ?? "watch"}`} aria-label="主图周期方向读取">
            <div>
              <span className="marketAiSectionLabel">主图方向 · {reportSnapshot?.bar || "当前"} K线</span>
              <strong>{marketAiReadableText(directionSummary?.headline)}</strong>
              <small>{marketAiReadableText(directionSummary?.statusLabel)}</small>
            </div>
            <div className="marketAiDirectionSummaryPrice">
              <span>{marketAiReadableText(directionSummary?.confirmationPriceLabel)}</span>
              <strong>{formatValue(directionSummary?.confirmationPrice)}</strong>
              <small>{marketAiReadableText(directionSummary?.statusLabel)} · {directionSummary?.snapshot?.bar || reportSnapshot?.bar || "当前"} K线</small>
            </div>
            <p className="marketAiDirectionSummaryMet"><b>{marketAiReadableText(directionSummary?.metLabel) || "已满足"}</b>{marketAiReadableText(directionSummary?.metCondition)}</p>
            <p className="marketAiDirectionSummaryNext"><b>{marketAiReadableText(directionSummary?.missingLabel) || "还差"}</b>{marketAiReadableText(directionSummary?.missingCondition || directionSummary?.nextCondition)}</p>
            <small className="marketAiDirectionSummaryBoundary">{marketAiReadableText(directionSummary?.readOnly)}</small>
          </section> : null}
          <section className={`marketAiMultiTimeframe ${multiTimeframeTrend.alignmentState}`} aria-label="多周期趋势">
            <div className="marketAiMultiTimeframeHeader">
              <div>
                <span className="marketAiSectionLabel">多周期趋势</span>
                <strong>{multiTimeframeTrend.alignment}</strong>
              </div>
              <small>各周期独立 K线快照</small>
            </div>
            <div className="marketAiMultiTimeframeGrid">
              {multiTimeframeTrend.periods.map((period) => (
                <article key={period.key ?? period.bar} className={`${period.trend ?? "unavailable"} ${period.available ? "available" : "unavailable"}`}>
                  <div>
                    <span>{marketAiReadableText(period.label)}</span>
                    <strong>{marketAiReadableText(period.trendLabel)}</strong>
                  </div>
                  {period.available ? (
                    <p>{(period.evidence ?? []).slice(0, 2).map(marketAiReadableText).join("；")}</p>
                  ) : (
                    <p>{marketAiReadableText(period.warning) || "该周期数据待获取。"}</p>
                  )}
                  <small><b>确认后重读</b>{marketAiReadableText(period.condition)}</small>
                </article>
              ))}
            </div>
            <small className="marketAiMultiTimeframeBoundary">趋势仅用于阅读当前行情快照；不是下单或个人化投资建议。</small>
          </section>
          <Disclosure className="marketAiScenarioDetails" label="查看双向条件与场景依据">
          <div className="marketAiScenarioBoardHeader">
            <div>
              <span className="marketAiSectionLabel">当前市场状态</span>
              <strong>{marketAiReadableText(scenarioBoard.marketState?.label)}</strong>
              <p>{marketAiReadableText(scenarioBoard.marketState?.summary)}</p>
            </div>
            <div className="marketAiScenarioScore">
              <span>场景证据度</span>
              <strong>{scenarioEvidenceScore}%</strong>
              <small>规则快照</small>
            </div>
          </div>
          <p className="marketAiScenarioScoreMeaning">{marketAiReadableText(scenarioBoard.scoreMeaning)}</p>
          <div className="marketAiScenarioStateGrid">
            <article><span>当前价格</span><strong>{formatValue(scenarioBoard.marketState?.price)}</strong><small>{reportSnapshot?.bar || "当前"} K线快照</small></article>
            <article><span>观察区</span><strong>{formatValue(scenarioBoard.marketState?.rangeLow)} – {formatValue(scenarioBoard.marketState?.rangeHigh)}</strong><small>{marketAiReadableText(scenarioBoard.marketState?.positionLabel)}{scenarioBoard.marketState?.positionPct ? ` · 区间 ${scenarioBoard.marketState.positionPct}%` : ""}</small></article>
            <article><span>当前线索</span><strong>{marketAiReadableText(scenarioBoard.marketState?.strongestClue?.label) || "暂无单侧线索"}</strong><small>{marketAiReadableText(scenarioBoard.marketState?.strongestClue?.detail) || "等待价格与结构出现同向变化。"}</small></article>
          </div>
          {scenarioBoard.dataLimitations?.length ? (
            <div className="marketAiScenarioLimitations" aria-label="场景数据限制">
              <strong>完整确认暂受限</strong>
              {scenarioBoard.dataLimitations.map((item) => <p key={item.label}><span>{marketAiReadableText(item.label)}</span>{marketAiReadableText(item.detail)}</p>)}
            </div>
          ) : null}
          <div className="marketAiScenarioCandidateGrid">
            {scenarioBoard.candidates?.slice(0, 2).map((candidate) => (
              <article key={candidate.key ?? candidate.label} className={`${candidate.tone === "bearish" ? "bearish" : "bullish"} ${candidate.status ?? "watch"}`}>
                <div><span>{marketAiReadableText(candidate.label)}</span><strong>{formatValue(candidate.confirmationPrice)}</strong><small>{marketAiReadableText(candidate.statusLabel)}</small></div>
                <p><b>价格条件</b>{marketAiReadableText(candidate.priceCondition)}</p>
                <p><b>{marketAiReadableText(candidate.distanceLabel)}</b>{formatValue(candidate.distance)}</p>
                {candidate.missingEvidence?.length ? <p><b>仍缺证据</b>{candidate.missingEvidence.map((item) => `${marketAiReadableText(item.label)}：${marketAiReadableText(item.detail)}`).join("；")}</p> : null}
                {candidate.limitations?.length ? <p className="marketAiScenarioCandidateLimit"><b>数据限制</b>{candidate.limitations.map((item) => `${marketAiReadableText(item.label)}：${marketAiReadableText(item.detail)}`).join("；")}</p> : null}
                <p><b>重读条件</b>{marketAiReadableText(candidate.invalidation)}</p>
              </article>
            ))}
          </div>
          <small className="marketAiScenarioReadOnly">条件仅用于阅读当前行情快照；不是成交、下单或个人化投资建议。</small>
          </Disclosure>
        </section>
      ) : null}

      {outlook && decision ? (
        <Disclosure className="marketAiEvidenceDetails" label="查看证据详情、AI 文字解读与数据来源">
        <section className={`marketAiDecision ${decision.assessment ?? "insufficient"}`} aria-label="决策参考">
          <div className="marketAiDecisionHeader">
            <div>
              <span className="marketAiSectionLabel">决策参考</span>
              <strong>{marketAiDirectionLayerLabel(decision)}</strong>
              <p>{marketAiReadableText(decision.summary)}</p>
              <small className="marketAiDecisionExplainer">{marketAiDirectionLayerExplanation(decision)}</small>
            </div>
            <div className="marketAiDecisionPills">
              <span>{marketAiDecisionAssessmentLabel(decision.assessment)}</span>
              <span>场景证据度 {scenarioEvidenceScore}%</span>
              <span>{marketAiDataQualityLabel(decision.dataQuality)}</span>
            </div>
          </div>
          <div className="marketAiDecisionConditions">
            <p><span>关注条件</span>{marketAiReadableText(decision.condition)}</p>
            <p><span>重评条件</span>{marketAiReadableText(decision.invalidation)}</p>
          </div>
          <section className="marketAiConfidenceBasis" aria-label="证据充分度依据">
            <div className="marketAiConfidenceBasisHeader">
              <div>
                <span className="marketAiSectionLabel">证据充分度依据</span>
                <strong>为什么是 {confidenceExplanation.referenceValue ?? scenarioEvidenceScore}%？</strong>
              </div>
              <small>不是涨跌概率</small>
            </div>
            <p className="marketAiConfidenceMeaning">{marketAiReadableText(confidenceExplanation.referenceMeaning)}</p>
            <p className="marketAiConfidenceSource"><strong>{marketAiReadableText(confidenceExplanation.sourceLabel)}</strong>{marketAiReadableText(confidenceExplanation.sourceReason)}</p>
            <div className="marketAiConfidenceStatusGrid">
              <article>
                <span>图表方向</span>
                <strong>{marketAiReadableText(confidenceExplanation.chartDirection?.label)}</strong>
                <small>{marketAiReadableText(confidenceExplanation.chartDirection?.gap) || "先由本次 K线快照判断是否存在明确方向。"}</small>
              </article>
              <article>
                <span>方向确认</span>
                <strong>{marketAiReadableText(confidenceExplanation.confirmation?.label)}</strong>
                <small>{marketAiReadableText(confidenceExplanation.confirmation?.summary)}</small>
              </article>
              <article>
                <span>交易数据</span>
                <strong>{marketAiReadableText(confidenceExplanation.dataAvailability?.label)}</strong>
                <small>数据已获取不等于已经形成可靠方向。</small>
              </article>
            </div>
            <p className="marketAiPeriodProvenance" aria-label="图表与交易结构周期">{periodProvenance.label}</p>
            {evidenceGaps.length ? (
              <div className="marketAiEvidenceGapGrid" aria-label="证据缺口">
                {evidenceGaps.map((item) => (
                  <article key={item.key ?? item.label} className={!item.available ? "unavailable" : item.signal === "up" ? "up" : item.signal === "down" ? "down" : ""}>
                    <span>{marketAiStructureLabel(item)}</span>
                    <strong>{marketAiConfidenceEvidenceValue(item)} · {marketAiReadableText(item.statusLabel)}</strong>
                    <small><b>确认门槛</b>{marketAiReadableText(item.threshold)}</small>
                    <small><b>当前缺口</b>{marketAiReadableText(item.gap)}</small>
                    <em>{marketAiReadableText(item.contribution)}</em>
                  </article>
                ))}
              </div>
            ) : null}
          </section>
          {confirmationLevels && !outlook?.scenarioBoard ? (
            <section className="marketAiConfirmationLevels" aria-label="条件确认价">
              <div className="marketAiConfirmationLevelsHeader">
                <div>
                  <span className="marketAiSectionLabel">下一步观察</span>
                  <strong>{marketAiReadableText(confirmationLevels.currentState.label)}</strong>
                  <p>{marketAiReadableText(confirmationLevels.currentState.summary)}</p>
                </div>
                <small>{observationLevelState}</small>
              </div>
              <div className="marketAiConfirmationCandidateGrid">
                {confirmationLevels.candidates.map((candidate) => (
                  <article key={candidate.key ?? candidate.label} className={candidate.tone === "bearish" ? "bearish" : "bullish"}>
                    <div className="marketAiConfirmationCandidateHeader">
                      <span>{marketAiReadableText(candidate.label)}</span>
                      <strong>{formatValue(candidate.confirmationPrice)}</strong>
                      <small>{marketAiReadableText(candidate.priceMeaning)}</small>
                    </div>
                    <div className="marketAiConfirmationRequirements">
                      {candidate.requirements?.map((requirement) => (
                        <p key={requirement.label ?? requirement.detail}>
                          <span>{marketAiReadableText(requirement.label)}</span>
                          {marketAiReadableText(requirement.detail)}
                        </p>
                      ))}
                    </div>
                    {candidate.missingEvidence?.length ? (
                      <p className="marketAiCandidateGap"><span>本侧仍缺</span>{candidate.missingEvidence.map((item) => `${marketAiReadableText(item.label)}：${marketAiReadableText(item.detail)}`).join("；")}</p>
                    ) : null}
                    <p className="marketAiConfirmationStatus"><span>当前状态</span><strong>{marketAiReadableText(candidate.statusLabel)}</strong>{marketAiReadableText(candidate.statusDetail)}</p>
                    <p className="marketAiConfirmationInvalidation"><span>失效条件</span>{marketAiReadableText(candidate.invalidation)}</p>
                  </article>
                ))}
              </div>
              {observationLevels?.participationNote ? <p className="marketAiConfirmationNote">{marketAiReadableText(observationLevels.participationNote)}</p> : null}
            </section>
          ) : null}
          <div className="marketAiStructureHeader">
            <div>
              <span className="marketAiSectionLabel">交易结构依据</span>
              <strong>{tradingStructure?.period ? `OKX 合约统计 · ${tradingStructure.period}` : "交易统计待确认"}</strong>
            </div>
            <small>
              {tradingStructure?.ts ? `${periodProvenance.label} · 更新 ${new Date(tradingStructure.ts).toLocaleTimeString("zh-CN")}` : periodProvenance.label}
            </small>
          </div>
          <div className="marketAiStructureGrid">
            {structureItems.map((item) => (
              <article key={item.key ?? item.label} className={!item.available ? "unavailable" : item.signal === "up" ? "up" : item.signal === "down" ? "down" : ""}>
                <span>{marketAiStructureLabel(item)}</span>
                <strong>{marketAiStructureValue(item)}</strong>
                <small>{marketAiStructureStateLabel(item)}</small>
                {marketAiStructureExplanation(item) ? <em>{marketAiStructureExplanation(item)}</em> : null}
              </article>
            ))}
          </div>
          {tradingStructure?.warnings?.length ? <p className="marketAiStructureWarning">{tradingStructure.warnings.slice(0, 2).map(marketAiReadableText).join("；")}</p> : null}
        </section>
        </Disclosure>
      ) : null}

      {initialAnalysisLoading ? (
        <section className="marketAiLoadingSkeleton" aria-label="正在生成 AI 行情报告" aria-hidden="true">
          <div className="marketAiLoadingSkeletonDirection">
            <div>
              <span className="marketAiSkeletonLine label" />
              <span className="marketAiSkeletonLine title" />
              <span className="marketAiSkeletonLine text" />
              <span className="marketAiSkeletonLine text short" />
            </div>
            <div className="marketAiLoadingSkeletonPrice">
              <span className="marketAiSkeletonLine label" />
              <span className="marketAiSkeletonLine value" />
              <span className="marketAiSkeletonLine text short" />
            </div>
          </div>
          <div className="marketAiLoadingSkeletonPeriods">
            <span className="marketAiSkeletonLine label" />
            <span className="marketAiSkeletonLine heading" />
            <div className="marketAiLoadingSkeletonGrid">
              {["15m", "1H", "1D"].map((period) => (
                <article key={period}>
                  <span className="marketAiSkeletonLine label" />
                  <span className="marketAiSkeletonLine heading" />
                  <span className="marketAiSkeletonLine text" />
                  <span className="marketAiSkeletonLine text short" />
                </article>
              ))}
            </div>
          </div>
        </section>
      ) : <>
      <div className="marketAiReading">
        <article className={`marketAiConclusion ${marketAiStanceClass(outlook?.stance)}`}>
          <span className="marketAiSectionLabel">主图结构概览</span>
          <strong>{outlook ? (pricePlan ? marketAiReadableText(directionSummary?.headline) || marketAiOverallView(outlook) : marketAiOverallView(outlook)) : "等待手动分析"}</strong>
          <p>{outlook ? marketAiChartSummary(outlook) : "当前图表快照已就绪后，点击“开始分析”即可一次生成主图结论与固定三周期阅读。"}</p>
          <div className="marketAiStatusRow" aria-label="图表数据状态">
            <span>{snapshotState}</span>
            {reportSnapshot?.currentCandleOpen ? <span>本根 K线实时更新中</span> : null}
            {outlook ? <span>场景证据度 {scenarioEvidenceScore}%</span> : null}
          </div>
        </article>

        <section className="marketAiEvidence" aria-label="图表依据">
          <div className="marketAiSectionHeader">
            <div>
              <span className="marketAiSectionLabel">图表依据</span>
              <strong>{outlook ? `${reportSnapshot?.bar ?? "当前"} K线的可核对事实` : "等待分析后展示"}</strong>
            </div>
            <small>{outlook ? "最多展示三项" : "不会自动生成"}</small>
          </div>
          {primaryFacts.length ? (
            <div className="marketAiFactList">
              {primaryFacts.map((fact) => (
                <div key={`${fact.label}-${fact.value}`} className="marketAiFact">
                  <span>{fact.label}</span>
                  <strong>{fact.value}</strong>
                  {fact.detail ? <small>{fact.detail}</small> : null}
                </div>
              ))}
            </div>
          ) : (
            <p className="marketAiEmptyFact">{outlook ? "本次报告暂未返回可拆分的图表依据，可结合当前 K线重新阅读。" : "分析完成后会在这里展示价格区间、均线或量能等依据。"}</p>
          )}
        </section>
      </div>

      {forecasts.length ? (
        <section className="marketAiForecast" aria-label="条件推演">
          <div className="marketAiSectionHeader">
            <div>
              <span className="marketAiSectionLabel">条件推演</span>
              <strong>基于本次图表快照的短周期推演</strong>
            </div>
            <small>不是确定价格预测</small>
          </div>
          <div className={`marketAiForecastGrid count-${forecasts.length}`}>
            {forecasts.map((forecast) => (
              <article key={forecast.key} className="marketAiForecastCard">
                <div className="marketAiForecastCardHeader">
                  <span>{forecast.label}</span>
                  <small>置信度 {forecast.confidence}%</small>
                </div>
                <strong>{forecast.direction}</strong>
                <p>{forecast.summary}</p>
                <em><span>重读</span>{forecast.condition}</em>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <div className="marketAiFollowup">
        <section>
          <span className="marketAiSectionLabel">数据状态</span>
          <strong>{snapshotState}</strong>
          <p>{dataStatus}{reportSnapshot?.warning ? ` · ${marketAiSupplementaryWarning(reportSnapshot.warning)}` : ""}</p>
        </section>
        <section>
          <span className="marketAiSectionLabel">后续观察</span>
          <strong>{chartHasNewerSnapshot ? "图表已有新数据" : outlook ? "等待关键变化" : "等待分析"}</strong>
          <p>{chartHasNewerSnapshot ? "当前报告基于较早的图表快照；确认需要时可手动刷新后重读。" : marketAiReadableText([...focusItems, ...reassessItems].slice(0, 2).join("；")) || "当前图表出现明显变化后再重新阅读。"}</p>
        </section>
      </div>

      <Disclosure className={`marketAiSupplement ${externalSourceWarning ? "hasWarning" : ""}`} label={
        <>
          <span>补充数据与来源</span>
          <small>{externalSourceWarning ? "存在外部数据提示" : "宏观信息与来源"}</small>
        </>
      }>
        <div className="marketAiSupplementBody">
          <section>
            <strong>数据来源</strong>
            {analysisProfile ? (
              <p className="marketAiProfileProvenance" role="status" aria-live="polite">
                行情读取规则：公开行情只读 · {analysisProfile.id} v{analysisProfile.profileVersion}
              </p>
            ) : null}
            {sourceItems.length ? (
              <div className="marketAiSourceList">
                {sourceItems.map((item, index) =>
                  item.url ? (
                    <a key={`${item.title}-${index}`} href={item.url} target="_blank" rel="noreferrer">
                      {marketAiSourceTitle(item)}
                    </a>
                  ) : (
                    <span key={`${item.title}-${index}`}>{marketAiSourceTitle(item)}</span>
                  )
                )}
              </div>
            ) : (
              <p>报告生成后会在这里列出补充数据来源。</p>
            )}
          </section>
          <section>
            <strong>{externalSourceWarning ? "补充数据提示" : "参考提示"}</strong>
            <div className="marketAiSupplementList">
              {outlook?.macro?.drivers?.slice(0, 2).map((item) => <span key={item}>宏观补充：{marketAiReadableText(item)}</span>)}
              {supplementaryItems.slice(0, 4).map((item) => <span key={item}>{item}</span>)}
              {!externalSourceWarning ? <span>仅作行情阅读参考，不构成投资建议；宏观事件和 K线结构变化后需要重新阅读。</span> : null}
            </div>
          </section>
        </div>
      </Disclosure>
      </>}

      <p className="marketAiSafetyNote">仅供行情阅读参考 · 不会下单 · 不会影响自动交易</p>
    </Paper>
  );
}

function accountSourceLabel(source?: string) {
  if (!source) return "等待连接";
  if (source === "not-configured") return "未配置";
  if (source === "okx") return "OKX 实时";
  if (source === "okx-cache") return "内存缓存";
  if (source === "okx-stale-cache") return "缓存回退";
  if (source === "database-cache") return "数据库快照";
  if (source === "okx-unavailable") return "暂不可用";
  if (source === "error") return "暂不可用";
  return sourceLabel(source);
}

function accountFailureSnapshot(current: AccountResponse | null, label: string): AccountResponse {
  if (current?.configured && current.summary && Array.isArray(current.positions)) {
    const warning = `${label}暂时无法更新，已保留最近可用数据。`;
    return {
      ...current,
      source: "okx-stale-cache",
      warning,
      refresh: { ...current.refresh, state: "stale", label: warning }
    };
  }
  const warning = `${label}暂不可用，请稍后刷新。`;
  return { configured: false, summary: null, positions: [], message: warning, warning, source: "error" };
}

function tradeSourceLabel(source?: string) {
  if (!source) return "本地记录";
  if (source === "okx-sim") return "OKX 模拟盘";
  if (source === "okx-live") return "OKX 真实盘";
  if (source === "okx-sim-cache") return "虚拟盘缓存";
  if (source === "okx-live-cache") return "真实盘缓存";
  if (source === "okx-sim-stale-cache") return "虚拟盘缓存刷新中";
  if (source === "okx-live-stale-cache") return "真实盘缓存刷新中";
  if (source === "okx-sim-unavailable") return "虚拟盘 OKX 暂不可用";
  if (source === "okx-live-unavailable") return "真实盘 OKX 暂不可用";
  if (source === "local-refreshing") return "挂单后台同步中";
  if (source === "local") return "本地记录";
  return sourceLabel(source);
}

function environmentLabel(environment?: string) {
  if (environment === "simulated") return "虚拟盘";
  if (environment === "live") return "真实盘";
  return "--";
}

function tradeStatusLabel(settings?: SettingsStatus | null) {
  const environment = settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  if (!settings?.hasCredentials) return `${environmentLabel(environment)}未连接`;
  if (settings?.tradeEnabled) return `${environmentLabel(environment)}可下单`;
  if (environment === "live") return "真实盘只读";
  return "只读保护";
}

function tradeBlockedTitle(settings?: SettingsStatus | null) {
  const environment = settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  if (settings?.tradeEnabled) return "";
  if (!settings) return "交易状态加载中";
  if (!settings.hasCredentials) return `${environmentLabel(environment)} API 未配置`;
  if (environment === "live" && !settings.liveTradingEnabled) return "真实盘只读保护已开启";
  return "交易提交已锁定";
}

function tradeBlockedDetail(settings?: SettingsStatus | null) {
  const environment = settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  if (settings?.tradeEnabled) return "";
  if (!settings) return "正在读取后端交易状态，请稍后再试。";
  if (!settings.hasCredentials) return `当前${environmentLabel(environment)}缺少 API Key，暂时不能提交订单。`;
  if (environment === "live" && !settings.liveTradingEnabled) {
    return "当前允许查看真实盘行情和账户，但禁止真实下单。模拟下单请切回虚拟盘。";
  }
  return "后端交易保护当前未放行订单提交。";
}

function apiCredentialLabel(label: string, configured?: boolean) {
  return `${label} API ${configured ? "已配置" : "未配置"}`;
}

function orderActionLabel(action?: string) {
  if (action === "place") return "下单";
  if (action === "cancel") return "撤单";
  if (action === "close-position") return "市价全平";
  return action ?? "--";
}

function isReduceOnlyValue(value?: unknown) {
  return value === true || value === 1 || value === "1" || value === "true";
}

function orderTradeDirectionLabel(side?: string, reduceOnly?: unknown) {
  const isReduceOnly = isReduceOnlyValue(reduceOnly);
  if (side === "buy") return isReduceOnly ? "平空" : "做多";
  if (side === "sell") return isReduceOnly ? "平多" : "做空";
  return side ?? "--";
}

function posSideForTradeOrder(side: string, reduceOnly?: unknown) {
  const isReduceOnly = isReduceOnlyValue(reduceOnly);
  if (side === "buy") return isReduceOnly ? "short" : "long";
  if (side === "sell") return isReduceOnly ? "long" : "short";
  return "net";
}

function orderPosSideLabel(posSide?: string) {
  if (!posSide || posSide === "net") return "单向持仓";
  if (posSide === "long") return "多头仓位";
  if (posSide === "short") return "空头仓位";
  return posSide;
}

function orderDirectionLabel(side?: string, posSide?: string, reduceOnly?: unknown) {
  const direction = orderTradeDirectionLabel(side, reduceOnly);
  const normalized = normalizedPositionSide(posSide);
  const expected = posSideForTradeOrder(String(side || ""), reduceOnly);
  return normalized === "net" || normalized === expected ? direction : `${direction} / ${orderPosSideLabel(normalized)}`;
}

function orderEventDirectionLabel(event: SimOrderEvent) {
  if (event.action === "close-position") {
    const posSide = normalizedPositionSide(event.pos_side);
    if (posSide === "long") return "平多";
    if (posSide === "short") return "平空";
    return "净持仓全平";
  }
  return orderDirectionLabel(event.side, event.pos_side, event.reduce_only);
}

function normalizedPositionSide(posSide?: string) {
  const value = String(posSide || "net").toLowerCase();
  return value === "long" || value === "short" || value === "net" ? value : "net";
}

function positionDirectionLabel(position: Record<string, string>) {
  const side = normalizedPositionSide(position.posSide);
  if (side !== "net") return orderPosSideLabel(side);
  const size = toNumber(position.pos);
  if (size !== null && size < 0) return "净空";
  if (size !== null && size > 0) return "净多";
  return "净持仓";
}

function positionMarginModeLabel(mode?: string) {
  if (mode === "cross") return "全仓";
  if (mode === "isolated") return "逐仓";
  return mode || "--";
}

function positionNumber(position: Record<string, string>, fields: string[]) {
  for (const field of fields) {
    const value = toNumber(position[field]);
    if (value !== null) return value;
  }
  return null;
}

function positionText(position: Record<string, string>, fields: string[], fallback = "--") {
  for (const field of fields) {
    const value = position[field];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return fallback;
}

function positionQuantityUnit(position: Record<string, string>) {
  const positionCurrency = positionText(position, ["posCcy"], "");
  if (positionCurrency) return positionCurrency.toUpperCase();
  const instType = positionText(position, ["instType"], "").toUpperCase();
  if (instType === "SWAP" || instType === "FUTURES" || instType === "OPTION") return "张";
  return "";
}

function positionQuantityText(position: Record<string, string>, fields: string[]) {
  const value = positionText(position, fields);
  if (value === "--") return value;
  const unit = positionQuantityUnit(position);
  return unit ? `${formatValue(value)} ${unit}` : formatValue(value);
}

function positionIsOpen(position: Record<string, string>) {
  const size = positionNumber(position, ["pos"]);
  return size !== null && Math.abs(size) > 0;
}

function positionCloseSize(position: Record<string, string>) {
  const available = positionNumber(position, ["availPos"]);
  if (available !== null && Math.abs(available) > 0) return formatOrderNumber(Math.abs(available), 8);
  const size = positionNumber(position, ["pos"]);
  if (size !== null && Math.abs(size) > 0) return formatOrderNumber(Math.abs(size), 8);
  return "";
}

function positionCloseOrder(position: Record<string, string>) {
  const instId = positionText(position, ["instId"], "").toUpperCase();
  const posSide = normalizedPositionSide(position.posSide);
  const size = positionNumber(position, ["pos"]) ?? 0;
  const closeSize = positionCloseSize(position);
  if (!instId || !closeSize) return null;

  if (posSide === "long") return { instId, side: "sell", posSide: "long", label: "平多", sz: closeSize };
  if (posSide === "short") return { instId, side: "buy", posSide: "short", label: "平空", sz: closeSize };
  if (size > 0) return { instId, side: "sell", posSide: "net", label: "平净多", sz: closeSize };
  if (size < 0) return { instId, side: "buy", posSide: "net", label: "平净空", sz: closeSize };
  return null;
}

function positionCloseTradeMode(position: Record<string, string>) {
  const mode = String(position.mgnMode || "").toLowerCase();
  return mode === "isolated" ? "isolated" : "cross";
}

function positionCloseModeLabel(mode: PositionCloseMode) {
  return positionCloseModeOptions.find((item) => item.key === mode)?.label ?? mode;
}

function positionCloseModeShortLabel(mode: PositionCloseMode) {
  return positionCloseModeOptions.find((item) => item.key === mode)?.shortLabel ?? positionCloseModeLabel(mode);
}

function positionCloseModeHint(mode: PositionCloseMode) {
  return positionCloseModeOptions.find((item) => item.key === mode)?.hint ?? "";
}

function positionDefaultClosePrice(position: Record<string, string>) {
  const price = positionText(position, ["markPx", "last", "idxPx", "avgPx"], "");
  return price === "--" ? "" : price;
}

function positionCloseModeOrderType(mode: PositionCloseMode) {
  if (mode === "limit_reduce") return "limit";
  if (mode === "market_reduce") return "market";
  return "";
}

function orderTypeLabel(ordType?: string) {
  return orderTypeOptions.find((item) => item.key === ordType)?.label ?? ordType ?? "--";
}

// 手动下单的幂等键：前缀 + 时间戳 + 随机串，符合 OKX clOrdId ≤32 位字母数字约束。
// 同一次提交意图内复用（存于 ref），网络重试不会生成新键，避免重复成交。
function makeClientOrderId(): string {
  const prefix = "OKXQ";
  const stamp = Date.now().toString(36).toUpperCase();
  const entropy = Math.random().toString(36).slice(2, 10).toUpperCase();
  return `${prefix}${stamp}${entropy}`.slice(0, 32);
}

function orderStateLabel(state?: string) {
  if (state === "live") return "挂单中";
  if (state === "partially_filled") return "部分成交";
  if (state === "filled") return "已成交";
  if (state === "canceled") return "已撤销";
  if (state === "accepted") return "已提交";
  if (state === "cancel_requested") return "撤单已提交";
  if (state === "close_requested") return "平仓已提交";
  if (state === "failed") return "失败";
  if (state === "rejected") return "已拒绝";
  return state ?? "--";
}

function orderStateClass(state?: string) {
  if (state === "failed" || state === "rejected") return "down";
  if (state === "live" || state === "partially_filled" || state === "accepted" || state === "close_requested") return "up";
  return "";
}

function orderNeedsPrice(ordType: string) {
  return ["limit", "post_only", "fok", "ioc"].includes(ordType);
}

function formatTime(value?: string | number | null) {
  if (value === undefined || value === null || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  return new Date(numeric).toLocaleString("zh-CN", { hour12: false });
}

// 列表里的时间统一格式化为「时:分:秒」（补零），副行给日期提示。
function formatClockSecond(value?: string | number | null) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  const date = new Date(numeric);
  if (!Number.isFinite(date.getTime())) return "--";
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

function formatDayHint(value?: string | number | null) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "";
  const target = new Date(numeric);
  if (!Number.isFinite(target.getTime())) return "";
  const startOfDay = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const dayDiff = Math.round((startOfDay(new Date()) - startOfDay(target)) / 86400000);
  if (dayDiff === 0) return "今天";
  if (dayDiff === 1) return "昨天";
  const month = String(target.getMonth() + 1).padStart(2, "0");
  const day = String(target.getDate()).padStart(2, "0");
  return `${month}-${day}`;
}

function formatDuration(ms?: number | null) {
  if (ms === undefined || ms === null || !Number.isFinite(ms)) return "--";
  if (ms < 1000) return "刚刚";
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}秒`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}分钟`;
  const hours = Math.floor(minutes / 60);
  return `${hours}小时`;
}

function formatEarnRate(value?: string | null) {
  if (value === undefined || value === null || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return value;
  const percent = Math.abs(numeric) > 1 ? numeric : numeric * 100;
  return `${percent.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}%`;
}

function earnTermLabel(term?: string | null) {
  if (!term) return "--";
  return term === "0" ? "活期" : `${term} 天`;
}

function earnRedeemPeriodLabel(period?: string[]) {
  if (!period?.length) return "--";
  return period.length === 1 || period[0] === period[period.length - 1] ? period[0] : `${period[0]}-${period[period.length - 1]}`;
}

function earnAmountText(items?: EarnDataItem[], keys: Array<keyof EarnDataItem> = ["amt", "bal"]) {
  if (!items?.length) return "--";
  return items
    .map((item) => {
      const value = keys.map((key) => item[key]).find((candidate) => candidate !== undefined && candidate !== null && candidate !== "");
      return value ? `${formatValue(String(value))} ${item.ccy ?? ""}`.trim() : "";
    })
    .filter(Boolean)
    .join(" / ") || "--";
}

function earnInvestRangeText(items?: EarnDataItem[]) {
  if (!items?.length) return "--";
  return items
    .map((item) => {
      const parts = [];
      if (item.minAmt) parts.push(`最低 ${formatValue(item.minAmt)}`);
      if (item.maxAmt) parts.push(`最高 ${formatValue(item.maxAmt)}`);
      if (!parts.length && item.bal) parts.push(`可用 ${formatValue(item.bal)}`);
      return parts.length ? `${parts.join(" / ")} ${item.ccy ?? ""}`.trim() : "";
    })
    .filter(Boolean)
    .join(" / ") || "--";
}

function earnEarningsText(items?: EarnDataItem[]) {
  if (!items?.length) return "--";
  return items
    .map((item) => {
      const value = item.earnings || item.realizedEarnings;
      const label = item.earningTypeLabel ? `${item.earningTypeLabel} ` : "";
      return value ? `${label}${formatValue(value)} ${item.ccy ?? ""}`.trim() : "";
    })
    .filter(Boolean)
    .join(" / ") || "--";
}

function earnStateClass(state?: string) {
  if (state === "purchasable" || state === "1" || state === "success") return "up";
  if (state === "sold_out" || state === "stop" || state === "failed") return "down";
  if (state === "2" || state === "8" || state === "9" || state === "13" || state === "pending") return "warning";
  return "";
}

function stakingHistoryTypeLabel(type?: string) {
  if (type === "purchase") return "申购";
  if (type === "redeem") return "赎回";
  return type || "--";
}

function isUsdtSettled(instrument: Instrument) {
  return instrumentSettlementKind(instrument, instrument.inst_id) === "usdt";
}

function isCoinSettled(instrument: Instrument) {
  return instrumentSettlementKind(instrument, instrument.inst_id) === "coin";
}

function instrumentMatchesKeyword(instrument: Instrument, keyword: string) {
  if (!keyword) return true;
  const settlementLabel = instrumentSettlementLabel(instrument, instrument.inst_id);
  const summaryLabel = instrumentSummaryLabel(instrument, instrument.inst_id);
  const displaySymbol = instrumentDisplaySymbol(instrument.inst_id);
  const assetName = instrumentAssetName(instrument, instrument.inst_id).toUpperCase();
  return (
    instrument.inst_id.includes(keyword) ||
    displaySymbol.includes(keyword) ||
    assetName.includes(keyword) ||
    (instrument.inst_family ?? "").includes(keyword) ||
    (instrument.settle_ccy ?? "").includes(keyword) ||
    settlementLabel.includes(keyword) ||
    summaryLabel.includes(keyword) ||
    (instrument.ct_val ?? "").includes(keyword) ||
    (instrument.ct_val_ccy ?? "").includes(keyword)
  );
}

function instrumentMatchesFilter(instrument: Instrument, filter: InstrumentFilter) {
  if (filter === "watch") return Boolean(instrument.watched);
  if (filter === "usdt") return isUsdtSettled(instrument);
  if (filter === "coin") return isCoinSettled(instrument);
  if (filter === "live") return instrument.state === "live";
  return true;
}

function accountDetails(summary: Record<string, unknown>): AccountDetail[] {
  return Array.isArray(summary.details) ? (summary.details as AccountDetail[]) : [];
}

function sumDetails(details: AccountDetail[], fields: string[]) {
  return details.reduce((total, item) => {
    const value = fields.find((field) => item[field] !== undefined && item[field] !== "");
    return total + (value ? Number(item[value] ?? 0) : 0);
  }, 0);
}

function firstMetric(summary: Record<string, unknown>, details: AccountDetail[], topField: string, detailFields: string[]) {
  const topValue = summary[topField];
  if (typeof topValue === "string" && topValue !== "") return topValue;
  const detailValue = sumDetails(details, detailFields);
  return detailValue === 0 ? "" : String(detailValue);
}

function accountDetailNumber(detail: AccountDetail, fields: string[]) {
  for (const field of fields) {
    const value = toNumber(detail[field]);
    if (value !== null) return value;
  }
  return null;
}

function accountDetailText(detail: AccountDetail, fields: string[], fallback = "--") {
  for (const field of fields) {
    const value = detail[field];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return fallback;
}

function accountDetailCurrency(detail: AccountDetail) {
  return accountDetailText(detail, ["ccy"], "--").toUpperCase();
}

function accountDetailIsNonZero(detail: AccountDetail) {
  return ["eq", "eqUsd", "availEq", "availBal", "cashBal", "frozenBal", "ordFrozen", "imr", "mmr", "isoEq", "upl"].some(
    (field) => Math.abs(toNumber(detail[field]) ?? 0) > 0
  );
}

function accountDetailAnyNonZero(detail: AccountDetail, fields: string[]) {
  return fields.some((field) => Math.abs(toNumber(detail[field]) ?? 0) > 0);
}

function accountDetailUsdValue(detail: AccountDetail) {
  return accountDetailNumber(detail, ["eqUsd"]) ?? 0;
}

function marginCurrencyForInstrument(instrument: Instrument | undefined, instId: string) {
  const fallback = instrumentCurrencies(instId).quote;
  return String(instrument?.settle_ccy || fallback || "").toUpperCase();
}

function availableBalanceForCurrency(account: AccountResponse | null, ccy: string) {
  if (!account?.summary || !ccy) return null;
  const detail = accountDetails(account.summary).find((item) => String(item.ccy || "").toUpperCase() === ccy.toUpperCase());
  if (!detail) return null;
  for (const field of ["availEq", "availBal", "cashBal", "eq"]) {
    const value = toNumber(detail[field]);
    if (value !== null) return value;
  }
  return null;
}

function leverageForPosition(rows: LeverageInfo[], posSide: string) {
  const normalized = posSide === "long" || posSide === "short" ? posSide : "net";
  const row =
    rows.find((item) => String(item.posSide || "net").toLowerCase() === normalized) ??
    rows.find((item) => String(item.posSide || "net").toLowerCase() === "net") ??
    rows[0];
  return toNumber(row?.lever);
}

function formatLeverage(value?: number | null) {
  return value !== undefined && value !== null && value > 0 ? `${formatOrderNumber(value, 2)}x` : "--";
}

function leverageRowsSummary(rows: LeverageInfo[]) {
  const longLeverage = leverageForPosition(rows, "long");
  const shortLeverage = leverageForPosition(rows, "short");
  if (
    longLeverage &&
    shortLeverage &&
    Math.abs(longLeverage - shortLeverage) > 0.000001 &&
    rows.some((item) => String(item.posSide || "").toLowerCase() === "long")
  ) {
    return `多 ${formatLeverage(longLeverage)} / 空 ${formatLeverage(shortLeverage)}`;
  }
  return formatLeverage(leverageForPosition(rows, "net"));
}

function leverageScopeLabel(tdMode: string, posSide: string) {
  if (tdMode === "isolated") {
    if (posSide === "long") return "逐仓多头";
    if (posSide === "short") return "逐仓空头";
    return "逐仓单向";
  }
  return "全仓";
}

function parseLeverageInput(value: string) {
  const normalized = value.trim().replace(/[xX倍]/g, "");
  return toNumber(normalized);
}

function estimatedMarginForContracts(
  quantityEstimate: {
    base: string;
    quote: string;
    baseAmount: number | null;
    quoteAmount: number | null;
  },
  marginCurrency: string,
  leverage: number | null
) {
  if (!leverage || leverage <= 0) return null;
  const normalizedMarginCurrency = marginCurrency.toUpperCase();
  if (normalizedMarginCurrency === quantityEstimate.base && quantityEstimate.baseAmount) {
    return { amount: quantityEstimate.baseAmount / leverage, currency: quantityEstimate.base };
  }
  if (normalizedMarginCurrency === quantityEstimate.quote && quantityEstimate.quoteAmount) {
    return { amount: quantityEstimate.quoteAmount / leverage, currency: quantityEstimate.quote };
  }
  if (quantityEstimate.quoteAmount) {
    return { amount: quantityEstimate.quoteAmount / leverage, currency: quantityEstimate.quote };
  }
  if (quantityEstimate.baseAmount) {
    return { amount: quantityEstimate.baseAmount / leverage, currency: quantityEstimate.base };
  }
  return null;
}

function orderEventMessage(event: SimOrderEvent) {
  const code = String(event.code || "").trim();
  const message = String(event.message || "").trim();
  if (code === "0") return message;
  const marginMatch = message.match(/Insufficient\s+([A-Z]+)\s+margin/i);
  if (code === "51008" && marginMatch?.[1]) return `${marginMatch[1]} 保证金不足，OKX 已拒单。（OKX 51008）`;
  if (code === "51008") return "保证金不足，OKX 已拒单。（OKX 51008）";
  if (code === "51000" && message.includes("posSide")) return "账户持仓模式与下单方向不匹配。（OKX 51000）";
  if (code === "51001") return "该合约不在当前账户可下单范围内。（OKX 51001）";
  if (code === "50123") return "API Key 没有该品种交易权限。（OKX 50123）";
  if (code && message) return `${message}（OKX ${code}）`;
  return message || (code ? `OKX ${code}` : "");
}

function automationExecutionModeLabel(mode?: string) {
  if (mode === "simulated_auto") return "模拟盘自动";
  if (mode === "signal_only") return "只提醒";
  return mode ?? "--";
}

function automationTemplateLabel(template?: string) {
  if (template === "llm_direct") return "LLM 判断";
  if (template === "ma_cross") return "均线交叉";
  return template ?? "--";
}

function automationActionLabel(action?: string) {
  if (action === "long") return "做多";
  if (action === "short") return "做空";
  if (action === "hold") return "观望";
  if (action === "take_profit") return "止盈";
  if (action === "stop_loss") return "止损";
  return action ?? "--";
}

function automationDecisionLabel(decision?: string) {
  if (decision === "submitted") return "已提交虚拟盘";
  if (decision === "signal_only") return "仅记录信号";
  if (decision === "skipped") return "已跳过";
  if (decision === "blocked") return "风控拦截";
  if (decision === "llm_failed") return "AI失败";
  if (decision === "failed") return "执行失败";
  if (decision === "observed") return "观察记录";
  return decision ?? "--";
}

function automationDecisionClass(decision?: string) {
  if (decision === "submitted" || decision === "signal_only") return "up";
  if (decision === "blocked" || decision === "failed" || decision === "llm_failed") return "down";
  if (decision === "skipped") return "warning";
  return "";
}

function automationEnabledLabel(enabled?: boolean) {
  return enabled ? "运行中" : "已暂停";
}

function automationActionClass(action?: string) {
  if (action === "long") return "up";
  if (action === "short") return "down";
  if (action === "take_profit") return "up";
  if (action === "stop_loss") return "down";
  return "";
}

function automationStyleLabel(fast?: string | number, slow?: string | number) {
  const matched = automationStylePresets.find((item) => item.fast === String(fast) && item.slow === String(slow));
  return matched?.label ?? "自定义";
}

function automationStrategyStyleLabel(strategy: Pick<AutomationStrategy, "template" | "fast_window" | "slow_window">) {
  if (strategy.template === "llm_direct") return "LLM 直接判断";
  return automationStyleLabel(strategy.fast_window, strategy.slow_window);
}

function automationExecutionActionLabel(action?: string) {
  if (action === "open") return "开新仓";
  if (action === "reverse") return "平仓反手";
  if (action === "close_opposite") return "平反向仓";
  if (action === "skip_same_direction") return "跳过加仓";
  if (action === "none") return "不执行";
  return action ?? "--";
}

function latestStrategySignal(signals: AutomationSignal[], strategyId: number) {
  return signals.find((item) => item.strategy_id === strategyId) ?? null;
}

function riskStatusLabel(status?: string) {
  if (status === "pass") return "通过";
  if (status === "warn") return "注意";
  if (status === "block") return "拦截";
  return status ?? "--";
}

function riskStatusClass(status?: string) {
  if (status === "pass") return "up";
  if (status === "warn") return "warning";
  if (status === "block") return "down";
  return "";
}

function previewSeverityClass(severity?: string) {
  if (severity === "ok") return "ok";
  if (severity === "blocked") return "blocked";
  return "warning";
}

function automationArchiveStateLabel(strategy: Pick<AutomationStrategy, "enabled" | "archived">) {
  if (strategy.archived) return "已归档";
  return strategy.enabled ? "已启用" : "已暂停";
}

function automationAlertSeverityLabel(value?: string) {
  if (value === "critical") return "严重";
  if (value === "warning") return "提醒";
  return value ?? "--";
}

function automationAlertSeverityClass(value?: string) {
  if (value === "critical") return "down";
  if (value === "warning") return "warning";
  return "";
}

function automationAlertSourceLabel(value?: string) {
  if (value === "global_pause") return "全局暂停";
  if (value === "circuit_breaker") return "熔断";
  if (value === "risk_block") return "风控";
  if (value === "execution_error") return "执行异常";
  if (value === "llm_failure") return "LLM 失败";
  return value ?? "--";
}

function automationAlertStateLabel(alert: AutomationAlert) {
  return alert.active ? "未确认" : "已确认";
}

function automationGlobalStateLabel(status?: AutomationStatus | null) {
  if (status?.globalStateAvailable === false) return "安全状态不可读 · 已停止交易";
  if (status?.globalPaused) return "全局暂停中";
  if (status?.circuitBreakerActive) return "已触发熔断";
  return "正常";
}

function executionStepStatusLabel(value?: string) {
  if (value === "ok" || value === "success") return "成功";
  if (value === "failed" || value === "error") return "失败";
  return value ?? "--";
}

function executionStepStatusClass(value?: string) {
  if (value === "ok" || value === "success") return "up";
  if (value === "failed" || value === "error") return "down";
  return "warning";
}

function formatPercentPoint(value?: string | null) {
  if (value === undefined || value === null || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return `${value}%`;
  return `${numeric.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}%`;
}

function backtestSideLabel(side?: string) {
  if (side === "long") return "做多";
  if (side === "short") return "做空";
  return side ?? "--";
}

function signalRawPayload(signal: AutomationSignal) {
  if (!signal.raw_json) return null;
  try {
    const parsed = JSON.parse(signal.raw_json);
    return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function signalRiskSnapshot(signal: AutomationSignal): AutomationRiskSnapshot | null {
  const snapshot = signal.riskSnapshot;
  if (!snapshot || Array.isArray(snapshot) || typeof snapshot !== "object") {
    const raw = signalRawPayload(signal);
    const fallback = raw?.risk_snapshot;
    if (!fallback || typeof fallback !== "object" || Array.isArray(fallback)) return null;
    return fallback as AutomationRiskSnapshot;
  }
  return snapshot as AutomationRiskSnapshot;
}

function signalExecutionSteps(signal: AutomationSignal): AutomationExecutionStep[] {
  if (Array.isArray(signal.executionSteps)) {
    return signal.executionSteps as AutomationExecutionStep[];
  }
  const raw = signalRawPayload(signal);
  const fallback = raw?.execution_steps;
  return Array.isArray(fallback) ? (fallback as AutomationExecutionStep[]) : [];
}

function signalAlertPayload(alert: AutomationAlert) {
  if (alert.raw) return alert.raw;
  if (!alert.raw_json) return null;
  try {
    const parsed = JSON.parse(alert.raw_json);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function signalLlmAnalysis(signal: AutomationSignal): LlmAnalysis | null {
  const raw = signalRawPayload(signal);
  const analysis = raw?.llm_analysis;
  if (!analysis || typeof analysis !== "object" || Array.isArray(analysis)) return null;
  return analysis as LlmAnalysis;
}

function signalLlmFailure(signal: AutomationSignal): LlmAnalysis | null {
  const raw = signalRawPayload(signal);
  const error = typeof raw?.llm_error === "string" ? raw.llm_error : "";
  if (!error) return null;
  return {
    status: "failed",
    provider: typeof raw?.llm_provider === "string" ? raw.llm_provider : undefined,
    model: typeof raw?.llm_model === "string" ? raw.llm_model : undefined,
    mode: "direct_signal",
    summary: signal.reason || signal.message || "LLM 调用失败。",
    confidence: 0,
    error
  };
}

function normalizeLlmBaseUrl(value?: string) {
  return String(value || "").trim().replace(/\/+$/, "").toLowerCase();
}

function llmPresetBaseUrls(preset: LlmProviderPreset) {
  return [preset.baseUrl, ...(preset.aliases ?? [])].filter(Boolean).map((value) => normalizeLlmBaseUrl(value));
}

function llmProviderPresetByKey(key?: string) {
  return llmProviderPresets.find((item) => item.key === key) ?? llmProviderPresets[llmProviderPresets.length - 1];
}

function llmProviderPresetForConfig(config: Pick<LlmConfig, "provider" | "baseUrl">) {
  const normalizedBaseUrl = normalizeLlmBaseUrl(config.baseUrl);
  const matched = llmProviderPresets.find((item) => llmPresetBaseUrls(item).includes(normalizedBaseUrl));
  if (matched) return matched.key;
  if (config.provider === "custom") return "custom";
  return "openai";
}

function llmModelSelectValue(model: string, models: string[]) {
  return models.includes(model) ? model : "__custom__";
}

function llmModelNote(preset: LlmProviderPreset, model: string) {
  return preset.modelNotes?.[model] ?? "";
}

function llmConfigToForm(config: LlmConfig): LlmConfigForm {
  const providerPreset = llmProviderPresetForConfig(config);
  const preset = llmProviderPresetByKey(providerPreset);
  const baseUrl = preset.key !== "custom" && llmPresetBaseUrls(preset).includes(normalizeLlmBaseUrl(config.baseUrl))
    ? preset.baseUrl
    : config.baseUrl || preset.baseUrl || "";
  return {
    enabled: config.enabled,
    providerPreset,
    provider: config.provider || "openai_compatible",
    baseUrl,
    apiKey: "",
    clearApiKey: false,
    model: config.model || "",
    temperature: String(config.temperature ?? 0.2),
    maxTokens: String(config.maxTokens ?? 800),
    timeoutSeconds: String(config.effectiveTimeoutSeconds ?? config.timeoutSeconds ?? DEFAULT_LLM_TIMEOUT_SECONDS),
    systemPrompt: config.systemPrompt || defaultLlmSystemPrompt
  };
}

function llmModeLabel(mode?: string) {
  if (mode === "explain_only") return "只解释信号";
  if (mode === "review") return "复核信号";
  if (mode === "direct_signal") return "直接信号";
  return mode ?? "--";
}

function llmRecommendationLabel(value?: string) {
  if (value === "long") return "做多";
  if (value === "short") return "做空";
  if (value === "approve") return "建议通过";
  if (value === "reject") return "建议拒绝";
  if (value === "hold") return "建议观望";
  if (value === "observe") return "观察记录";
  return value ?? "--";
}

function llmRecommendationClass(value?: string) {
  if (value === "approve" || value === "long") return "up";
  if (value === "reject" || value === "short") return "down";
  if (value === "hold") return "warning";
  return "";
}

function llmUsageRequestTypeLabel(value?: string | null) {
  if (value === "direct_signal") return "直接信号";
  if (value === "signal_review") return "信号复核";
  if (value === "connection_test") return "连接测试";
  if (value === "unknown") return "未知调用";
  return value || "--";
}

function llmUsageStatusLabel(value?: string | null) {
  if (value === "success") return "成功";
  if (value === "failed") return "失败";
  if (value === "timeout") return "超时";
  return value || "--";
}

function llmUsageStatusClass(value?: string | null) {
  if (value === "success") return "up";
  if (value === "failed" || value === "timeout") return "down";
  return "";
}

function formatTokenCount(value?: number | null) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return "--";
  return numeric.toLocaleString("zh-CN");
}

function formatLatency(value?: number | null) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric) || numeric <= 0) return "--";
  if (numeric >= 1000) return `${(numeric / 1000).toLocaleString("zh-CN", { maximumFractionDigits: 2 })} 秒`;
  return `${numeric.toLocaleString("zh-CN")} ms`;
}

function compactRequestId(value?: string | null) {
  if (!value) return "--";
  return value.length > 12 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

function parseRawUsage(value?: string | null) {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function signalLlmUsage(signal: AutomationSignal): Partial<LlmUsageLog> | null {
  const raw = signalRawPayload(signal);
  const directUsage = raw?.llm_usage;
  if (directUsage && typeof directUsage === "object" && !Array.isArray(directUsage)) {
    return directUsage as Partial<LlmUsageLog>;
  }
  const analysis = raw?.llm_analysis;
  if (analysis && typeof analysis === "object" && !Array.isArray(analysis)) {
    const usage = (analysis as LlmAnalysis).usage;
    if (usage && typeof usage === "object" && !Array.isArray(usage)) return usage;
  }
  return null;
}

function signalReason(signal: AutomationSignal) {
  return signal.reason || String(signalRawPayload(signal)?.reason || "") || signal.message || "--";
}

function signalCandleTime(signal: AutomationSignal) {
  const raw = signalRawPayload(signal);
  const candleTs = Number(raw?.candle_ts || 0);
  return candleTs ? formatTime(candleTs) : "--";
}

function signalOkxOrderText(signal: AutomationSignal) {
  const raw = signalRawPayload(signal);
  const side = signal.side || (typeof raw?.side === "string" ? raw.side : "");
  const posSide = signal.pos_side || (typeof raw?.pos_side === "string" ? raw.pos_side : "");
  if (!side && !posSide) return "--";
  return `${orderDirectionLabel(side, posSide)} (${side || "--"} / ${posSide || "net"})`;
}

function parseMaSignalReason(reason?: string) {
  const text = reason || "";
  const currentMatch = text.match(/MA(\d+)=([^，,。]+)[，,]\s*MA(\d+)=([^，,。]+)/);
  const previousMatch = text.match(/上一根\s*MA(\d+)=([^，,。]+)[，,]\s*MA(\d+)=([^，,。]+)/);
  if (!currentMatch && !previousMatch) return null;
  return {
    fastLabel: currentMatch?.[1] ?? previousMatch?.[1] ?? "--",
    slowLabel: currentMatch?.[3] ?? previousMatch?.[3] ?? "--",
    currentFast: currentMatch?.[2]?.trim() ?? "--",
    currentSlow: currentMatch?.[4]?.trim() ?? "--",
    previousFast: previousMatch?.[2]?.trim() ?? "--",
    previousSlow: previousMatch?.[4]?.trim() ?? "--"
  };
}

function signalWhyText(signal: AutomationSignal) {
  const reason = signalReason(signal);
  if (signal.action === "long") {
    return `做多原因：上一根快线还没有明显站上慢线，当前快线已经上穿慢线，系统判断短期价格强于中期趋势。${reason}`;
  }
  if (signal.action === "short") {
    return `做空原因：上一根快线还没有明显跌破慢线，当前快线已经下穿慢线，系统判断短期价格弱于中期趋势。${reason}`;
  }
  if (signal.action === "hold") {
    return `观望原因：当前没有满足做多或做空条件，系统没有产生可执行交易方向。${reason}`;
  }
  return reason;
}

const defaultAppRoute: AppRouteState = {
  section: "market",
  marketTab: "radar",
  automationTab: "overview",
  accountTab: "positions",
  settingsTab: "llm",
  signalDetailId: null,
  selectedContract: "BTC-USDT-SWAP",
  selectedBar: "1m",
  timelineDate: new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai" }).format(new Date())
};

function normalizeRouteContract(value?: string | null) {
  const normalized = (value ?? "").trim().toUpperCase();
  return normalized.endsWith("-SWAP") ? normalized : defaultAppRoute.selectedContract;
}

function normalizeRouteBar(value?: string | null) {
  const normalized = (value ?? "").trim();
  return bars.includes(normalized) ? normalized : defaultAppRoute.selectedBar;
}

function normalizeTimelineDate(value?: string | null) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value ?? "") ? String(value) : defaultAppRoute.timelineDate;
}

function parsePositiveRouteId(value?: string) {
  const id = Number(value ?? "");
  return Number.isInteger(id) && id > 0 ? id : null;
}

function readAppRouteFromHash(hash: string): AppRouteState {
  const [rawPath, rawQuery = ""] = hash.replace(/^#/, "").split("?");
  const parts = rawPath.split("/").filter(Boolean);
  const params = new URLSearchParams(rawQuery);
  const route: AppRouteState = {
    ...defaultAppRoute,
    selectedContract: normalizeRouteContract(params.get("inst")),
    selectedBar: normalizeRouteBar(params.get("bar")),
    timelineDate: normalizeTimelineDate(params.get("date"))
  };

  if (parts[0] === "market") {
    route.section = "market";
    route.marketTab =
      parts[1] === "overview"
        ? "overview"
        : parts[1] === "announcements"
        ? "announcements"
        : parts[1] === "stats"
          ? "stats"
          : parts[1] === "ai-outlook"
            ? "aiOutlook"
            : parts[1] === "ai-records"
              ? "aiRecords"
            : parts[1] === "us-timeline"
              ? "usTimeline"
            : parts[1] === "chart"
              ? "chart"
              : "radar";
  } else if (parts[0] === "trade") {
    route.section = "trade";
  } else if (parts[0] === "orders") {
    route.section = "orders";
  } else if (parts[0] === "automation") {
    route.section = "automation";
    if (parts[1] === "strategies") {
      route.automationTab = "strategies";
    } else if (parts[1] === "signals" && parts[2]) {
      route.automationTab = "signalDetail";
      route.signalDetailId = parsePositiveRouteId(parts[2]);
      if (!route.signalDetailId) route.automationTab = "signals";
    } else if (parts[1] === "signals") {
      route.automationTab = "signals";
    } else {
      route.automationTab = "overview";
    }
  } else if (parts[0] === "account") {
    route.section = "account";
    route.accountTab = parts[1] === "earn" ? "earn" : parts[1] === "account" ? "account" : "positions";
  } else if (parts[0] === "settings") {
    route.section = "settings";
    route.settingsTab = parts[1] === "usage" ? "usage" : "llm";
  }

  return route;
}

function routeQueryString(route: AppRouteState) {
  const params = new URLSearchParams();
  if (route.section === "market" && route.marketTab === "aiOutlook") {
    params.set("inst", route.selectedContract);
  } else if (
    route.selectedContract !== defaultAppRoute.selectedContract &&
    ((route.section === "market" && route.marketTab === "chart") ||
      (route.section === "market" && route.marketTab === "stats") ||
      route.section === "trade" ||
      (route.section === "automation" && route.automationTab === "overview"))
  ) {
    params.set("inst", route.selectedContract);
  }
  if (route.section === "market" && route.marketTab === "usTimeline") params.set("date", normalizeTimelineDate(route.timelineDate));
  if (route.section === "market" && route.marketTab === "aiOutlook") {
    params.set("bar", normalizeRouteBar(route.selectedBar));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

function buildAppHash(route: AppRouteState) {
  let path = "/market/radar";
  if (route.section === "market") path = route.marketTab === "aiOutlook" ? "/market/ai-outlook" : route.marketTab === "aiRecords" ? "/market/ai-records" : route.marketTab === "usTimeline" ? "/market/us-timeline" : `/market/${route.marketTab}`;
  if (route.section === "trade") path = "/trade";
  if (route.section === "orders") path = "/orders";
  if (route.section === "automation") {
    path = route.automationTab === "signalDetail" && route.signalDetailId
      ? `/automation/signals/${route.signalDetailId}`
      : `/automation/${route.automationTab === "signalDetail" ? "signals" : route.automationTab}`;
  }
  if (route.section === "account") path = `/account/${route.accountTab}`;
  if (route.section === "settings") path = `/settings/${route.settingsTab}`;
  return `#${path}${routeQueryString(route)}`;
}

function SectionTabs({
  items
}: {
  items: Array<{ key: string; label: string; icon: React.ReactNode; active: boolean; onClick: () => void }>;
}) {
  const activeItem = items.find((item) => item.active);
  const tabsRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const container = tabsRef.current;
    const activeTab = container?.querySelector<HTMLElement>(".mantine-Tabs-tab[data-active]");
    if (!container || !activeTab || container.scrollWidth <= container.clientWidth) return;
    const tabLeft = activeTab.getBoundingClientRect().left - container.getBoundingClientRect().left + container.scrollLeft;
    container.scrollLeft = tabLeft - (container.clientWidth - activeTab.clientWidth) / 2;
  }, [activeItem?.key]);
  return (
    <Tabs
      ref={tabsRef}
      className="sectionTabs"
      value={activeItem?.key ?? null}
      onChange={(value) => items.find((item) => item.key === value)?.onClick()}
      aria-label="二级导航"
    >
      <Tabs.List>
        {items.map((item) => (
          <Tabs.Tab key={item.key} value={item.key} leftSection={item.icon} aria-current={item.active ? "page" : undefined}>
            {item.label}
          </Tabs.Tab>
        ))}
      </Tabs.List>
    </Tabs>
  );
}

function App() {
  const initialRoute = React.useMemo(() => readAppRouteFromHash(window.location.hash), []);
  const [section, setSection] = React.useState<PrimarySection>(initialRoute.section);
  const [marketTab, setMarketTab] = React.useState<MarketTab>(initialRoute.marketTab);
  const [automationTab, setAutomationTab] = React.useState<AutomationTab>(initialRoute.automationTab);
  const [accountTab, setAccountTab] = React.useState<AccountTab>(initialRoute.accountTab);
  const [settingsTab, setSettingsTab] = React.useState<SettingsTab>(initialRoute.settingsTab);
  const [signalDetailId, setSignalDetailId] = React.useState<number | null>(initialRoute.signalDetailId);
  const [strategyEditId, setStrategyEditId] = React.useState<number | null>(null);
  // 从策略列表点「新建策略」时置为 true，概览页消费后打开空白表单。
  const [strategyCreateIntent, setStrategyCreateIntent] = React.useState(false);
  const [selectedContract, setSelectedContract] = React.useState(initialRoute.selectedContract);
  const [selectedBar, setSelectedBar] = React.useState(initialRoute.selectedBar);
  const [timelineDate, setTimelineDate] = React.useState(initialRoute.timelineDate);
  const [marketWorkbenchInitialFilter, setMarketWorkbenchInitialFilter] = React.useState<InstrumentFilter | null>(null);

  const applyRoute = React.useCallback((route: AppRouteState) => {
    setSection(route.section);
    setMarketTab(route.marketTab);
    setAutomationTab(route.automationTab);
    setAccountTab(route.accountTab);
    setSettingsTab(route.settingsTab);
    setSignalDetailId(route.signalDetailId);
    setSelectedContract(route.selectedContract);
    setSelectedBar(route.selectedBar);
    setTimelineDate(route.timelineDate);
    setStrategyEditId(null);
    setMarketWorkbenchInitialFilter(null);
  }, []);

  React.useEffect(() => {
    const handleRouteChange = () => applyRoute(readAppRouteFromHash(window.location.hash));
    window.addEventListener("hashchange", handleRouteChange);
    window.addEventListener("popstate", handleRouteChange);
    return () => {
      window.removeEventListener("hashchange", handleRouteChange);
      window.removeEventListener("popstate", handleRouteChange);
    };
  }, [applyRoute]);

  React.useEffect(() => {
    const nextHash = buildAppHash({
      section,
      marketTab,
      automationTab,
      accountTab,
      settingsTab,
      signalDetailId,
      selectedContract,
      selectedBar,
      timelineDate
    });
    if (window.location.hash !== nextHash) {
      const nextUrl = `${window.location.pathname}${window.location.search}${nextHash}`;
      if (window.location.hash) {
        window.history.pushState(null, "", nextUrl);
      } else {
        window.history.replaceState(null, "", nextUrl);
      }
    }
  }, [accountTab, automationTab, marketTab, section, selectedBar, selectedContract, settingsTab, signalDetailId, timelineDate]);

  const openSignalDetail = React.useCallback((signalId: number) => {
    setSignalDetailId(signalId);
    setSection("automation");
    setAutomationTab("signalDetail");
  }, []);

  const openRadarContract = React.useCallback((instId: string, target: RadarActionTarget) => {
    setSelectedContract(instId);
    if (target === "market") {
      setMarketWorkbenchInitialFilter("all");
      setSection("market");
      setMarketTab("chart");
    } else if (target === "aiOutlook") {
      setMarketWorkbenchInitialFilter("all");
      setSection("market");
      setMarketTab("aiOutlook");
    } else if (target === "stats") {
      setMarketWorkbenchInitialFilter("all");
      setSection("market");
      setMarketTab("stats");
    } else if (target === "trade") {
      setMarketWorkbenchInitialFilter(null);
      setSection("trade");
    } else {
      setMarketWorkbenchInitialFilter(null);
      setSection("automation");
      setAutomationTab("overview");
    }
  }, []);

  const openMarketAiOutlook = React.useCallback((instId: string, bar: string) => {
    setMarketWorkbenchInitialFilter(null);
    setSelectedContract(normalizeRouteContract(instId));
    setSelectedBar(normalizeRouteBar(bar));
    setSection("market");
    setMarketTab("aiOutlook");
    setSignalDetailId(null);
  }, []);

  const openStrategyEditor = React.useCallback((strategyId: number) => {
    setStrategyCreateIntent(false);
    setStrategyEditId(strategyId);
    setSection("automation");
    setAutomationTab("overview");
  }, []);

  const openStrategyCreator = React.useCallback(() => {
    setStrategyEditId(null);
    setStrategyCreateIntent(true);
    setSection("automation");
    setAutomationTab("overview");
  }, []);

  const openPrimarySection = (nextSection: PrimarySection) => {
    setMarketWorkbenchInitialFilter(null);
    setSection(nextSection);
    if (nextSection === "market") setMarketTab("radar");
    if (nextSection === "automation") setAutomationTab("overview");
    if (nextSection === "account") setAccountTab("positions");
    if (nextSection === "settings") setSettingsTab("llm");
    setSignalDetailId(null);
  };

  const secondaryTabs =
    section === "market" ? (
      <SectionTabs
        items={[
          {
            key: "overview",
            label: "市场概况",
            icon: <BarChart3 size={15} />,
            active: marketTab === "overview",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("overview");
            }
          },
          {
            key: "radar",
            label: "合约雷达",
            icon: <Search size={15} />,
            active: marketTab === "radar",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("radar");
            }
          },
          {
            key: "chart",
            label: "行情图表",
            icon: <ChartCandlestick size={15} />,
            active: marketTab === "chart",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("chart");
            }
          },
          {
            key: "aiOutlook",
            label: "AI看行情",
            icon: <BrainCircuit size={15} />,
            active: marketTab === "aiOutlook",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("aiOutlook");
            }
          },
          {
            key: "aiRecords",
            label: "预测记录",
            icon: <ClipboardList size={15} />,
            active: marketTab === "aiRecords",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("aiRecords");
            }
          },
          {
            key: "usTimeline",
            label: "美国事件",
            icon: <CalendarDays size={15} />,
            active: marketTab === "usTimeline",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("usTimeline");
            }
          },
          {
            key: "stats",
            label: "交易数据",
            icon: <Database size={15} />,
            active: marketTab === "stats",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("stats");
            }
          },
          {
            key: "announcements",
            label: "公告",
            icon: <Megaphone size={15} />,
            active: marketTab === "announcements",
            onClick: () => {
              setMarketWorkbenchInitialFilter(null);
              setMarketTab("announcements");
            }
          }
        ]}
      />
    ) : section === "automation" ? (
      <SectionTabs
        items={[
          { key: "overview", label: "概览", icon: <Bot size={15} />, active: automationTab === "overview", onClick: () => setAutomationTab("overview") },
          { key: "strategies", label: "策略", icon: <ClipboardList size={15} />, active: automationTab === "strategies", onClick: () => setAutomationTab("strategies") },
          {
            key: "signals",
            label: "信号",
            icon: <BookOpen size={15} />,
            active: automationTab === "signals" || automationTab === "signalDetail",
            onClick: () => {
              setAutomationTab("signals");
              setSignalDetailId(null);
            }
          }
        ]}
      />
    ) : section === "account" ? (
      <SectionTabs
        items={[
          { key: "positions", label: "持仓", icon: <WalletCards size={15} />, active: accountTab === "positions", onClick: () => setAccountTab("positions") },
          { key: "account", label: "账户", icon: <UserCog size={15} />, active: accountTab === "account", onClick: () => setAccountTab("account") },
          { key: "earn", label: "链上赚币", icon: <TrendingUp size={15} />, active: accountTab === "earn", onClick: () => setAccountTab("earn") }
        ]}
      />
    ) : section === "settings" ? (
      <SectionTabs
        items={[
          { key: "llm", label: "AI 配置", icon: <BrainCircuit size={15} />, active: settingsTab === "llm", onClick: () => setSettingsTab("llm") },
          { key: "usage", label: "AI 用量", icon: <BarChart3 size={15} />, active: settingsTab === "usage", onClick: () => setSettingsTab("usage") }
        ]}
      />
    ) : null;

  return (
    <AppShell header={{ height: { base: 96, sm: 60 } }} padding={0} className="appShell">
      <AppShell.Header className="appHeader">
        <div className="brandBlock">
          <div className="brandMark">
            <Activity size={20} aria-hidden="true" />
          </div>
          <div>
            <strong>OKX Quant</strong>
            <span>永续合约本地工作台</span>
          </div>
        </div>
        <nav className="topNav" aria-label="主导航">
          <Button variant={section === "market" ? "filled" : "subtle"} className={section === "market" ? "active" : ""} aria-current={section === "market" ? "page" : undefined} leftSection={<ChartCandlestick size={16} />} onClick={() => openPrimarySection("market")}>市场</Button>
          <Button variant={section === "trade" ? "filled" : "subtle"} className={section === "trade" ? "active" : ""} aria-current={section === "trade" ? "page" : undefined} leftSection={<Send size={16} />} onClick={() => openPrimarySection("trade")}>交易</Button>
          <Button variant={section === "orders" ? "filled" : "subtle"} className={section === "orders" ? "active" : ""} aria-current={section === "orders" ? "page" : undefined} leftSection={<Receipt size={16} />} onClick={() => openPrimarySection("orders")}>订单</Button>
          <Button variant={section === "automation" ? "filled" : "subtle"} className={section === "automation" ? "active" : ""} aria-current={section === "automation" ? "page" : undefined} leftSection={<Bot size={16} />} onClick={() => openPrimarySection("automation")}>自动化</Button>
          <Button variant={section === "account" ? "filled" : "subtle"} className={section === "account" ? "active" : ""} aria-current={section === "account" ? "page" : undefined} leftSection={<WalletCards size={16} />} onClick={() => openPrimarySection("account")}>账户</Button>
          <Button variant={section === "settings" ? "filled" : "subtle"} className={section === "settings" ? "active" : ""} aria-current={section === "settings" ? "page" : undefined} leftSection={<UserCog size={16} />} onClick={() => openPrimarySection("settings")}>设置</Button>
        </nav>
      </AppShell.Header>

      <AppShell.Main className="appShellMain">
      {secondaryTabs}

      {section === "market" && (marketTab === "chart" || marketTab === "aiOutlook" || marketTab === "stats") ? (
        <MarketContractWorkspace
          selected={selectedContract}
          activeBar={selectedBar}
          initialFilter={marketWorkbenchInitialFilter ?? (marketTab === "chart" ? "watch" : "usdt")}
          onSelectContract={setSelectedContract}
          onSelectBar={setSelectedBar}
        >
          {marketTab === "chart" ? (
            <MarketPage onOpenAiOutlook={openMarketAiOutlook} />
          ) : marketTab === "aiOutlook" ? (
            <MarketAiOutlookPage
              initialBar={selectedBar}
              onOpenChart={(instId, bar) => {
                setSelectedContract(normalizeRouteContract(instId));
                setSelectedBar(normalizeRouteBar(bar));
                setSection("market");
                setMarketTab("chart");
              }}
            />
          ) : (
            <MarketStatsPage />
          )}
        </MarketContractWorkspace>
      ) : section === "market" && marketTab === "overview" ? (
        <MarketOverviewPage onOpenChart={(instId) => { setSelectedContract(instId); setMarketTab("chart"); }} onOpenEvents={() => setMarketTab("usTimeline")} />
      ) : section === "market" && marketTab === "announcements" ? (
        <AnnouncementsPage />
      ) : section === "market" && marketTab === "aiRecords" ? (
        <MarketAiRecordsPage />
      ) : section === "market" && marketTab === "usTimeline" ? (
        <UsMarketTimelinePage date={timelineDate} onDateChange={setTimelineDate} />
      ) : section === "market" ? (
        <ContractRadarPage onOpenContract={openRadarContract} />
      ) : section === "trade" ? (
        <TradingPage initialInstId={selectedContract} onOpenOrders={() => openPrimarySection("orders")} />
      ) : section === "orders" ? (
        <OrdersPage onOpenTrade={() => openPrimarySection("trade")} />
      ) : section === "automation" && automationTab === "overview" ? (
        <CleanAutomationPage
          initialInstId={selectedContract}
          initialEditStrategyId={strategyEditId}
          initialCreate={strategyCreateIntent}
          onCreateConsumed={() => setStrategyCreateIntent(false)}
          onEditConsumed={() => setStrategyEditId(null)}
          onOpenStrategies={() => setAutomationTab("strategies")}
          onOpenSignals={() => setAutomationTab("signals")}
          onOpenLlm={() => {
            setSection("settings");
            setSettingsTab("llm");
          }}
          onOpenSignalDetail={openSignalDetail}
        />
      ) : section === "automation" && automationTab === "strategies" ? (
        <StrategyListPage onBackToAutomation={() => setAutomationTab("overview")} onEditStrategy={openStrategyEditor} onCreateStrategy={openStrategyCreator} />
      ) : section === "automation" && automationTab === "signals" ? (
        <SignalLogPage onOpenSignalDetail={openSignalDetail} />
      ) : section === "automation" ? (
        <SignalDetailPage signalId={signalDetailId} onBack={() => setAutomationTab("signals")} />
      ) : section === "account" && accountTab === "positions" ? (
        <PositionsPage />
      ) : section === "account" && accountTab === "account" ? (
        <AccountPage />
      ) : section === "account" ? (
        <EarnPage />
      ) : section === "settings" && settingsTab === "llm" ? (
        <LlmSettingsPage />
      ) : section === "settings" ? (
        <LlmUsagePage />
      ) : (
        <ContractRadarPage onOpenContract={openRadarContract} />
      )}
      </AppShell.Main>
    </AppShell>
  );
}

function radarRiskLabel(value?: string) {
  if (value === "low") return "风险较低";
  if (value === "medium") return "需要注意";
  if (value === "high") return "风险较高";
  return "风险待确认";
}

function radarRiskSummary(value?: string) {
  if (value === "low") return "暂未发现明显异常";
  if (value === "medium") return "有几项需要注意";
  if (value === "high") return "风险较高，谨慎观察";
  return "数据不足，暂时无法判断";
}

function radarVolatilityLabel(value?: string) {
  if (value === "low") return "低波动";
  if (value === "medium") return "中波动";
  if (value === "high") return "高波动";
  return "--";
}

function radarTradabilityLabel(value?: string) {
  if (value === "playable") return "可玩";
  if (value === "watch_only") return "仅观察";
  if (value === "low_liquidity") return "流动性不足";
  return "待确认";
}

function radarLiquidityBasisLabel(liquidity?: RadarLiquidity) {
  if (liquidity?.displayLabel) return liquidity.displayLabel;
  if (liquidity?.basis === "quote_turnover") return `24h 成交额${liquidity.unit ? `(${liquidity.unit})` : ""}`;
  if (liquidity?.basis === "estimated_quote_turnover") return `24h 估算成交额${liquidity.unit ? `(${liquidity.unit})` : ""}`;
  if (liquidity?.basis === "base_volume") return "24h 基础币量";
  if (liquidity?.basis === "contract_volume") return "24h 合约张数";
  if (liquidity?.basis === "legacy_volume") return "24h 量(旧缓存)";
  return "24h 流动性";
}

function radarLiquidityValue(result: RadarResult) {
  return result.liquidity?.value || result.volume24h || "";
}

function radarComparableTurnoverValue(result: RadarResult) {
  if (
    result.liquidity?.comparable === false ||
    (result.liquidity?.basis && !["quote_turnover", "estimated_quote_turnover"].includes(result.liquidity.basis))
  ) return null;
  const value = Number(radarLiquidityValue(result));
  return Number.isFinite(value) && value >= 0 ? value : null;
}

function radarResultMinimumTurnover(value: string) {
  const normalized = value.replace(/,/g, "").trim();
  if (!normalized) return 0;
  const amount = Number(normalized);
  return Number.isFinite(amount) && amount > 0 ? amount : 0;
}

function radarLiquidityCompact(result: RadarResult) {
  const value = radarLiquidityValue(result);
  const unit = result.liquidity?.unit && result.liquidity.basis !== "quote_turnover" ? ` ${result.liquidity.unit}` : "";
  return `${formatCompact(value)}${unit}`;
}

function radarSortLabel(sortBy?: string) {
  return sortBy === "turnover_24h" ? "24小时成交额" : "1小时成交额";
}

function radarTurnoverWindow(result: RadarResult, sortBy?: string) {
  if (sortBy === "turnover_24h") {
    return result.turnover?.twentyFourHour ?? {
      value: radarLiquidityValue(result),
      unit: result.liquidity?.unit,
      comparable: result.liquidity?.comparable,
      label: radarSortLabel(sortBy)
    };
  }
  return result.turnover?.oneHour ?? {
    value: "",
    comparable: false,
    label: radarSortLabel(sortBy),
    warning: "小时成交额待重新扫描。"
  };
}

function radarTurnoverCompact(result: RadarResult, sortBy?: string) {
  const turnover = radarTurnoverWindow(result, sortBy);
  if (!turnover.comparable || !turnover.value) return "待补齐";
  const unit = turnover.unit && turnover.unit !== "USDT" ? ` ${turnover.unit}` : "";
  return `${formatCompact(turnover.value)}${unit}`;
}

function radarWarningText(value?: string) {
  if (!value) return "";
  const normalized = value.toLowerCase();
  if (normalized.includes("incompleteread") || normalized.includes("remote end closed") || normalized.includes("okx response was incomplete")) {
    return "部分合约 K线暂时无法更新，已使用可用缓存或降级数据；可稍后重新扫描。";
  }
  return value;
}

function radarScoreClass(value?: number) {
  if ((value ?? 0) >= 75) return "up";
  if ((value ?? 0) >= 45) return "neutral";
  return "down";
}

function radarEntryLabel(value?: RadarEntryAssessment) {
  if (value?.label) return value.label;
  if (value?.status === "ready") return "可入手观察";
  if (value?.status === "wait") return "等待放量";
  if (value?.status === "avoid") return "暂不入手";
  if (value?.status === "watch") return "谨慎观察";
  return "待判断";
}

function radarEntryClass(value?: RadarEntryAssessment) {
  if (value?.status === "ready") return "up";
  if (value?.status === "avoid") return "down";
  return "neutral";
}

function radarMarketCondition(value?: RadarMarketCondition) {
  return value ?? {
    key: "unknown",
    label: "方向待确认",
    summary: "市场状态待重新扫描确认。"
  };
}

function radarMarketRegimeLabel(value?: string) {
  if (value === "trend") return "趋势";
  if (value === "range") return "震荡";
  if (value === "risk-off") return "避险";
  if (value === "mixed") return "分化";
  return "待分析";
}

type RadarBiasView = { label: string; tone: "bull" | "bear" | "neutral" };

function radarBiasView(value?: string): RadarBiasView {
  if (value === "long") return { label: "偏多", tone: "bull" };
  if (value === "short") return { label: "偏空", tone: "bear" };
  return { label: "中性", tone: "neutral" };
}

function radarDirectionView(value?: string): RadarBiasView {
  if (value === "long") return { label: "多", tone: "bull" };
  if (value === "short") return { label: "空", tone: "bear" };
  return { label: "中性", tone: "neutral" };
}

function formatUsdCompact(value?: string) {
  const n = Number(value ?? "");
  if (!isFinite(n) || n <= 0) return "--";
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toFixed(0);
}

type RadarSentimentView = {
  label: string;
  tone: "bull" | "bear" | "neutral";
  fundingText: string;
  oiText: string;
};

function radarSentimentView(
  sentiment?: {
    funding?: { sampled?: number; positive?: number; negative?: number; neutral?: number; avgFundingRate?: string; avgFundingRatePct?: string };
    openInterest?: { sampled?: number; maxOiUsd?: string; medianOiUsd?: string };
  }
): RadarSentimentView | null {
  if (!sentiment) return null;
  const funding = sentiment.funding || {};
  const oi = sentiment.openInterest || {};
  const sampled = Number(funding.sampled ?? 0);
  if (!sampled) return null;
  const positive = Number(funding.positive ?? 0);
  const negative = Number(funding.negative ?? 0);
  const neutral = Number(funding.neutral ?? 0);
  const positiveRatio = positive / sampled;
  const avgPct = funding.avgFundingRatePct;
  let label: string;
  let tone: RadarSentimentView["tone"];
  if (positiveRatio >= 0.6) {
    label = "多头偏强";
    tone = "bull";
  } else if (negative / sampled >= 0.6) {
    label = "空头偏强";
    tone = "bear";
  } else {
    label = "多空均衡";
    tone = "neutral";
  }
  const fundingText = `多 ${positive} · 空 ${negative} · 平 ${neutral} ｜ 均值 ${avgPct ? `${avgPct}%` : "--"}`;
  const oiSampled = Number(oi.sampled ?? 0);
  const oiText = oiSampled
    ? `最大 ${formatUsdCompact(oi.maxOiUsd)} ｜ 中位 ${formatUsdCompact(oi.medianOiUsd)}（样本 ${oiSampled}）`
    : "暂无持仓数据";
  return { label, tone, fundingText, oiText };
}

const US_TIMELINE_CATEGORIES = [
  ["", "全部"],
  ["monetary,inflation,employment,growth,consumption,trade", "财经事件"],
  ["treasury", "美债事件"],
] as const;
const US_TIMELINE_STATES = [["", "全部"], ["scheduled", "预告"], ["released", "已公布"], ["revised", "已修正"], ["cancelled", "已取消"]] as const;

function shanghaiDate(value: Date) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai" }).format(value);
}

function shiftTimelineMonth(date: string, offset: number) {
  const [year, month, day] = date.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, month - 1 + offset, 1));
  const targetYear = shifted.getUTCFullYear();
  const targetMonth = shifted.getUTCMonth() + 1;
  const lastDay = new Date(Date.UTC(targetYear, targetMonth, 0)).getUTCDate();
  return `${targetYear}-${String(targetMonth).padStart(2, "0")}-${String(Math.min(day, lastDay)).padStart(2, "0")}`;
}

function shiftTimelineDate(date: string, offset: number) {
  const [year, month, day] = date.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, month - 1, day + offset));
  return `${shifted.getUTCFullYear()}-${String(shifted.getUTCMonth() + 1).padStart(2, "0")}-${String(shifted.getUTCDate()).padStart(2, "0")}`;
}

function timelineFocusWindow(date: string) {
  return { from: shiftTimelineDate(date, -6), to: shiftTimelineDate(date, 14) };
}

// 官方日历（BLS / BEA / Treasury）以英文标题入库，展示层统一转中文。
// 英文原文仍保留在悬浮 title 与官方来源链接里，方便与官方日程核对。
const US_EVENT_TITLE_ZH: Record<string, string> = {
  "Consumer Price Index": "美国 CPI（消费者物价指数）",
  "Producer Price Index": "美国 PPI（生产者物价指数）",
  "Employment Situation": "美国就业情况报告",
  "Job Openings and Labor Turnover": "JOLTS 职位空缺（美国）",
  "Gross Domestic Product": "美国 GDP（国内生产总值）",
  "Personal Income and Outlays": "美国个人收入与支出（PCE）",
  "International Trade in Goods and Services": "美国国际贸易（商品与服务）",
  "Initial Jobless Claims": "美国初请失业金人数",
  "Nonfarm Payrolls": "美国非农就业人数",
  "Retail Sales": "美国零售销售",
  "ISM Manufacturing PMI": "美国 ISM 制造业 PMI",
  "ISM Services PMI": "美国 ISM 服务业 PMI",
  "Consumer Confidence": "美国消费者信心指数",
  "Housing Starts": "美国新屋开工",
  "Existing Home Sales": "美国成屋销售",
  "Trade Balance": "美国贸易帐",
  "FOMC Meeting Minutes": "FOMC 会议纪要"
};

const US_EVENT_PROVIDER_ZH: Record<string, string> = {
  "Federal Reserve": "美联储",
  BLS: "美国劳工统计局",
  BEA: "美国经济分析局",
  "U.S. Treasury": "美国财政部"
};

function usEventProviderLabel(provider?: string) {
  const key = String(provider ?? "").trim();
  if (!key) return "官方来源";
  return US_EVENT_PROVIDER_ZH[key] ?? key;
}

function usEventDisplayTitle(event: Pick<UsMarketEvent, "title" | "provider">) {
  const officialTitle = US_EVENT_TITLE_ZH[event.title];
  if (officialTitle) return officialTitle;
  if (event.provider !== "Federal Reserve") return event.title;
  if (/会议与利率决议|政策声明与利率决定|利率决策/.test(event.title)) return "美联储利率决策（美国）";
  if (/经济预测摘要|经济预测/.test(event.title)) return "FOMC 经济预测（美国）";
  if (/新闻发布会/.test(event.title)) return "美联储新闻发布会（美国）";
  return event.title;
}

const OVERVIEW_CONTRACTS = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"] as const;
const OVERVIEW_EVENT_PAST_DAYS = 7;
const OVERVIEW_EVENT_FUTURE_DAYS = 31;

function overviewEventRelativeTime(timestamp: number) {
  const remaining = timestamp - Date.now();
  if (remaining <= 0) return "已公布";
  const days = Math.floor(remaining / 86_400_000);
  if (days >= 1) return `${days} 天后`;
  const hours = Math.floor(remaining / 3_600_000);
  if (hours >= 1) return `${hours} 小时后`;
  return "即将公布";
}

// 概览页的市场宽度直接复用 /api/tickers 全量快照：与合约列表、合约雷达同源，
// 不额外引入接口。排除 OKX 返回的 TEST 占位合约与无法计算涨跌的行。
function overviewMarketBreadth(tickers: Ticker[] | null | undefined) {
  const rows: Array<{ instId: string; change: number; turnover: number | null }> = [];
  for (const ticker of tickers ?? []) {
    const instId = String(ticker?.instId ?? "").toUpperCase();
    if (!instId.endsWith("-SWAP") || instId.startsWith("TEST")) continue;
    const change = tickerRolling24hChange(ticker).percent;
    if (change === null || !Number.isFinite(change)) continue;
    rows.push({ instId, change, turnover: instrumentQuoteTurnover(ticker) });
  }
  const total = rows.length;
  const up = rows.filter((row) => row.change > 0.0001).length;
  const down = rows.filter((row) => row.change < -0.0001).length;
  const flat = total - up - down;
  const changes = rows.map((row) => row.change).sort((left, right) => left - right);
  const medianChange = total ? changes[Math.floor(total / 2)] : null;
  const averageChange = total ? changes.reduce((sum, value) => sum + value, 0) / total : null;
  const hasTurnover = rows.some((row) => row.turnover !== null);
  const turnoverUsd = hasTurnover ? rows.reduce((sum, row) => sum + (row.turnover ?? 0), 0) : null;
  const ranked = [...rows].sort((left, right) => right.change - left.change);
  const gainers = ranked.filter((row) => row.change > 0).slice(0, 3);
  const losers = ranked.filter((row) => row.change < 0).slice(-3).reverse();
  const upRatio = total ? up / total : 0;
  const sentiment = !total ? "--" : upRatio >= 0.65 ? "普涨" : upRatio <= 0.35 ? "普跌" : "分化";
  return { total, up, down, flat, upRatio, medianChange, averageChange, turnoverUsd, gainers, losers, sentiment };
}

function overviewShanghaiTime(timestamp?: number | null) {
  if (!timestamp || !Number.isFinite(timestamp)) return "时间待确认";
  return new Date(timestamp).toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
}

// 成交额的多周期数值必须由真实日线累加得出。OKX 的 platform-24-volume 只提供
// 滚动 24h 单点，没有历史序列，所以「周/月/年」绝不能用 24h × 天数推算。
// 每个维度都取滚动的 N 个交易日，并与紧邻的上一等长窗口比较；窗口不足时明确
// 返回 incomplete，不伪造数字。
const VOLUME_PERIOD_CONFIG: Record<VolumePeriod, { label: string; days: number; bucketDays: number; buckets: number }> = {
  day: { label: "日", days: 1, bucketDays: 1, buckets: 14 },
  week: { label: "周", days: 7, bucketDays: 7, buckets: 12 },
  month: { label: "月", days: 30, bucketDays: 30, buckets: 12 },
  year: { label: "年", days: 365, bucketDays: 30, buckets: 12 }
};

function shortVolumeDate(value: string) {
  return value ? value.slice(5).replace("-", "/") : "--";
}

function aggregateVolumePeriod(daily: VolumeHistoryPoint[] | null | undefined, period: VolumePeriod) {
  const config = VOLUME_PERIOD_CONFIG[period];
  const sorted = (daily ?? [])
    .map((point) => ({ ...point, value: toNumber(point.volUsd) }))
    .filter((point) => point.value !== null && Number.isFinite(point.value) && point.value >= 0)
    .sort((left, right) => left.ts - right.ts || left.date.localeCompare(right.date)) as Array<VolumeHistoryPoint & { value: number }>;
  // 当日 K 线尚未收盘时只有几小时的量，拿它跟完整交易日比会显示 -95% 之类的
  // 假暴跌。把未收盘日排除在所有周期与环比之外，单独作为「今日至今」展示。
  const unfinished = sorted.length && sorted[sorted.length - 1].confirm === "0" ? sorted[sorted.length - 1] : null;
  const points = unfinished ? sorted.slice(0, -1) : sorted;
  const sum = (rows: Array<{ value: number }>) => rows.reduce((total, row) => total + row.value, 0);
  const currentRows = points.slice(-config.days);
  const previousRows = points.slice(-config.days * 2, -config.days);
  const current = currentRows.length ? sum(currentRows) : null;
  const hasPrevious = previousRows.length === config.days;
  const previous = hasPrevious ? sum(previousRows) : null;
  const changePct = current !== null && previous !== null && previous > 0 ? ((current - previous) / previous) * 100 : null;
  const currentStart = currentRows[0]?.date ?? "";
  const currentEnd = currentRows[currentRows.length - 1]?.date ?? "";
  const previousStart = hasPrevious ? previousRows[0]?.date ?? "" : "";
  const previousEnd = hasPrevious ? previousRows[previousRows.length - 1]?.date ?? "" : "";
  const rangeLabel = (start: string, end: string) => {
    if (!start) return "";
    if (start === end) return shortVolumeDate(start);
    // 跨年窗口必须带年份，否则 11/14–11/13 看起来像倒序。
    if (start.slice(0, 4) !== end.slice(0, 4)) return `${start.slice(0, 4)}/${shortVolumeDate(start)}–${end.slice(0, 4)}/${shortVolumeDate(end)}`;
    return `${shortVolumeDate(start)}–${shortVolumeDate(end)}`;
  };
  const trendRows = points.slice(-config.bucketDays * config.buckets);
  const trend: Array<{ label: string; value: number; isPrevious: boolean; startDate: string; endDate: string }> = [];
  // 从末尾往前分桶，保证最后两桶与「本期 / 上一周期」边界完全对齐；
  // 历史不足整桶时只让最靠前的一桶变短，不会错位。
  for (let end = trendRows.length; end > 0; end -= config.bucketDays) {
    const bucket = trendRows.slice(Math.max(0, end - config.bucketDays), end);
    if (!bucket.length) continue;
    const bucketStart = bucket[0].date;
    const bucketEnd = bucket[bucket.length - 1].date;
    const isPrevious = Boolean(previousStart) && bucketStart >= previousStart && bucketEnd <= previousEnd;
    trend.unshift({ label: bucketEnd.slice(5), value: sum(bucket), isPrevious, startDate: bucketStart, endDate: bucketEnd });
  }
  return {
    label: config.label,
    days: config.days,
    current,
    previous,
    changePct,
    coveredDays: currentRows.length,
    complete: currentRows.length === config.days,
    hasPrevious,
    currentRange: rangeLabel(currentStart, currentEnd),
    previousRange: rangeLabel(previousStart, previousEnd),
    startDate: currentStart,
    endDate: currentEnd,
    unfinishedToday: unfinished ? { date: unfinished.date, value: unfinished.value } : null,
    totalDays: points.length,
    trend
  };
}

function MarketOverviewPage({ onOpenChart, onOpenEvents }: { onOpenChart: (instId: string) => void; onOpenEvents: () => void }) {
  const [volume, setVolume] = React.useState<PlatformVolumeResponse | null>(null);
  const [volumeHistory, setVolumeHistory] = React.useState<VolumeHistoryResponse | null>(null);
  const [volumePeriod, setVolumePeriod] = React.useState<VolumePeriod>("day");
  const [tickers, setTickers] = React.useState<TickersResponse | null>(null);
  const [events, setEvents] = React.useState<UsMarketEventsResponse | null>(null);
  const [volumeLoading, setVolumeLoading] = React.useState(true);
  const [volumeHistoryLoading, setVolumeHistoryLoading] = React.useState(true);
  const [tickerLoading, setTickerLoading] = React.useState(true);
  const [eventsLoading, setEventsLoading] = React.useState(true);
  const [volumeError, setVolumeError] = React.useState("");
  const [volumeHistoryError, setVolumeHistoryError] = React.useState("");
  const [tickerError, setTickerError] = React.useState("");
  const [eventsError, setEventsError] = React.useState("");

  React.useEffect(() => {
    let active = true;
    let timer = 0;
    let ready = false;
    const load = async () => {
      if (document.hidden) return;
      setVolumeHistoryLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/market/overview/volume-history`);
        if (!response.ok) throw new Error("成交额历史加载失败");
        const payload = await response.json() as VolumeHistoryResponse;
        ready = Boolean(payload.data?.daily?.length);
        if (active) { setVolumeHistory(payload); setVolumeHistoryError(""); }
      } catch {
        if (active) setVolumeHistoryError("成交额历史读取失败，请稍后重试。");
      } finally {
        if (active) setVolumeHistoryLoading(false);
      }
    };
    // 首次构建约需十余秒：历史未就绪时 5 秒轮询，拿到数据后按分钟刷新。
    const tick = async () => {
      if (!active) return;
      await load();
      if (!active) return;
      timer = window.setTimeout(() => { void tick(); }, ready ? 60_000 : 5_000);
    };
    void tick();
    return () => { active = false; window.clearTimeout(timer); };
  }, []);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      if (document.hidden) return;
      setVolumeLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/market/overview/volume`);
        if (!response.ok) throw new Error("平台成交额加载失败");
        const payload = await response.json() as PlatformVolumeResponse;
        if (active) { setVolume(payload); setVolumeError(""); }
      } catch {
        if (active) setVolumeError("平台成交额读取失败，请稍后重试。已显示上次可用数据（如有）。");
      } finally {
        if (active) setVolumeLoading(false);
      }
    };
    void load();
    const timer = window.setInterval(() => { void load(); }, 60_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      if (document.hidden) return;
      setTickerLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/tickers`);
        if (!response.ok) throw new Error("合约行情加载失败");
        const payload = await response.json() as TickersResponse;
        if (active) { setTickers(payload); setTickerError(""); }
      } catch {
        if (active) setTickerError("合约行情读取失败，请稍后重试。已显示上次可用数据（如有）。");
      } finally {
        if (active) setTickerLoading(false);
      }
    };
    void load();
    const timer = window.setInterval(() => { void load(); }, TICKER_POLL_MS);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      if (document.hidden) return;
      setEventsLoading(true);
      try {
        const today = shanghaiDate(new Date());
        // 官方日历经常一次公布整月日程，只看未来两周会经常空窗。分两段读取
        // （过去 7 天 + 未来 31 天，均在后端的 31 天窗口上限内），再按 id 去重。
        const windows = [
          { from: shiftTimelineDate(today, -OVERVIEW_EVENT_PAST_DAYS), to: today },
          { from: today, to: shiftTimelineDate(today, OVERVIEW_EVENT_FUTURE_DAYS) }
        ];
        const payloads = await Promise.all(windows.map(async ({ from, to }) => {
          const query = new URLSearchParams({ from, to });
          const response = await fetch(`${API_BASE}/api/market/us-events?${query}`);
          if (!response.ok) throw new Error("美国事件加载失败");
          return await response.json() as UsMarketEventsResponse;
        }));
        if (!active) return;
        const merged = new Map<string, UsMarketEvent>();
        for (const payload of payloads) {
          for (const event of payload.data ?? []) merged.set(event.id, event);
        }
        const primary = payloads[1];
        setEvents({
          ...primary,
          data: [...merged.values()],
          refreshing: payloads.some((payload) => payload.refreshing),
          warnings: [...new Set(payloads.flatMap((payload) => payload.warnings ?? []))]
        });
        setEventsError("");
      } catch {
        if (active) setEventsError("美国事件读取失败，请稍后重试。已显示上次可用日历（如有）。");
      } finally {
        if (active) setEventsLoading(false);
      }
    };
    void load();
    const timer = window.setInterval(() => { void load(); }, 60_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  const featured = OVERVIEW_CONTRACTS.map((instId) => ({ instId, ticker: tickers?.data?.find((item) => item.instId === instId) })).filter((item) => item.ticker);
  const breadth = React.useMemo(() => overviewMarketBreadth(tickers?.data), [tickers]);
  const now = Date.now();
  const calendarEvents = (events?.data ?? [])
    .filter((event) => event.state !== "cancelled" && typeof event.scheduledAt === "number" && Number.isFinite(event.scheduledAt))
    .sort((left, right) => (left.scheduledAt ?? 0) - (right.scheduledAt ?? 0));
  const futureEvents = calendarEvents.filter((event) => (event.scheduledAt ?? 0) >= now).slice(0, 4);
  const pastCount = Math.max(0, 4 - futureEvents.length);
  const pastEvents = pastCount
    ? calendarEvents.filter((event) => (event.scheduledAt ?? 0) < now).slice(-pastCount).reverse()
    : [];
  const overviewEvents = [
    ...futureEvents.map((event) => ({ event, upcoming: true })),
    ...pastEvents.map((event) => ({ event, upcoming: false }))
  ];
  const eventProviders = events?.providerStatuses ?? [];
  const healthyProviders = eventProviders.filter((provider) => provider.status === "fresh").length;
  const volumeAge = volume?.ts ? Date.now() - volume.ts : Infinity;
  const visibleVolume = volume?.data && volumeAge <= 15 * 60_000 ? volume.data : null;
  const volumeCached = Boolean(visibleVolume && (volume?.state !== "fresh" || volumeError));
  const platformVolUsd = toNumber(visibleVolume?.volUsd);
  const contractShare = platformVolUsd && platformVolUsd > 0 && breadth.turnoverUsd !== null
    ? (breadth.turnoverUsd / platformVolUsd) * 100
    : null;
  const volumeStats = React.useMemo(
    () => aggregateVolumePeriod(volumeHistory?.data?.daily, volumePeriod),
    [volumeHistory?.data?.daily, volumePeriod]
  );
  const volumeTrendMax = Math.max(...volumeStats.trend.map((point) => point.value), 1);
  const tickerRefresh = tickers?.refresh;
  // 后台正常刷新（failureCount=0、快照很新）不是故障，不应常驻橙色告警。
  const tickerStale = Boolean(tickers?.data?.length && (
    tickerError ||
    (tickerRefresh?.failureCount ?? 0) > 0 ||
    ["stale", "backing_off", "unavailable"].includes(tickerRefresh?.state ?? "") ||
    (tickerRefresh?.cacheAgeMs ?? 0) > 120_000
  ));

  return <section className="marketMain marketOverviewPage" aria-label="市场概况">
    <header className="marketOverviewHeader">
      <div><h1>市场概况</h1><p>OKX 平台成交额、代表合约行情、全市场宽度与近期美国事件。各项数据范围分别标注。</p></div>
    </header>
    <div className="marketOverviewGrid">
      <Paper component="section" className="marketOverviewPanel marketOverviewVolume" withBorder shadow="none" aria-label="OKX 成交额" aria-busy={volumeLoading || volumeHistoryLoading}>
        <div className="marketOverviewPanelHeader marketOverviewVolumeHeader">
          <div><h2>OKX 成交额（USD）</h2><p>主流永续合约 · 真实日线累加</p></div>
          <SegmentedControl aria-label="成交额统计周期" value={volumePeriod} onChange={(value) => setVolumePeriod(value as VolumePeriod)} data={[{ value: "day", label: "日" }, { value: "week", label: "周" }, { value: "month", label: "月" }, { value: "year", label: "年" }]} size="xs" />
        </div>
        {!volumeHistory?.data && volumeHistoryLoading ? <DataLoadingSkeleton label="正在累计 OKX 日线成交额" variant="metrics" /> : volumeStats.current !== null ? <>
          <strong className="marketOverviewBigNumber">{formatCompact(volumeStats.current)} <small>USD</small></strong>
          <div className="marketOverviewVolumeMeta">
            <span>{volumeStats.label}维度 · 近 {volumeStats.coveredDays} 个交易日累计</span>
            {volumeStats.changePct !== null ? <span className={changeClass(volumeStats.changePct)}>较上一周期（{volumeStats.previousRange}）{formatSignedPercent(volumeStats.changePct)}</span> : <span>上期数据不足，暂不计算环比</span>}
          </div>
          <div className="marketOverviewVolumeTrend" role="img" aria-label={`${volumeStats.label}维度成交额趋势，上一周期已高亮`}>
            {volumeStats.trend.map((point) => <span key={point.startDate} className={point.isPrevious ? "marketOverviewVolumeTrendPrevious" : undefined} title={`${point.startDate} ~ ${point.endDate}${point.isPrevious ? " · 上一周期" : ""} · ${formatCompact(point.value)} USD`} style={{ height: `${Math.max(4, (point.value / volumeTrendMax) * 100)}%` }} />)}
          </div>
          {volumeStats.hasPrevious ? <div className="marketOverviewVolumeLegend">
            <span><i className="marketOverviewLegendPrevious" />上一周期 {volumeStats.previousRange} · {formatCompact(volumeStats.previous ?? 0)} USD</span>
            <span><i className="marketOverviewLegendCurrent" />本期 {volumeStats.currentRange} · {formatCompact(volumeStats.current ?? 0)} USD</span>
          </div> : null}
          <p className="marketOverviewTrendCaption">按已收盘交易日统计 · {volumeStats.startDate} ~ {volumeStats.endDate}{!volumeStats.complete ? ` · 数据仅覆盖 ${volumeStats.coveredDays}/${volumeStats.days} 天，为部分周期累计` : ""}</p>
          {volumeStats.unfinishedToday ? <p className="marketOverviewTrendCaption">今日至今 {formatCompact(volumeStats.unfinishedToday.value)} USD（{volumeStats.unfinishedToday.date} 未收盘，未计入上述周期与环比）</p> : null}
        </> : <EmptyState compact>{volumeHistoryError || "成交额历史序列暂不可用，正在后台构建。"}</EmptyState>}
        {!volumeStats.complete && volumeStats.current !== null ? <Notice>所选周期的历史日线不足，当前数值为已覆盖交易日的真实累计，未做任何外推补齐。</Notice> : null}
        {volumeHistoryError && volumeStats.current !== null ? <Notice tone="warning">{volumeHistoryError}</Notice> : null}
        {visibleVolume ? <div className="marketOverviewVolumeComparison">
          <span><strong>{formatCompact(visibleVolume.volUsd)} USD</strong><small>官方 24h 全平台成交额{volumeCached ? " · 缓存" : ""}</small></span>
          <span><strong>{breadth.turnoverUsd === null ? "--" : `${formatCompact(breadth.turnoverUsd)} USD`}</strong><small>永续合约 24h 成交额（估算）{contractShare === null ? "" : ` · 占平台 ${contractShare.toFixed(1)}%`}</small></span>
        </div> : null}
        {volumeError && visibleVolume ? <Notice>{volumeError}</Notice> : null}
        {!visibleVolume && !volumeLoading ? <Notice tone="warning">官方 24h 全平台成交额暂不可用，上方多周期数值不受影响。</Notice> : null}
        <p className="marketOverviewSource">来源：OKX 1D 日线成交额（volumeQuote）累加{volumeHistory?.data ? ` · ${volumeHistory.data.instrumentCount} 个 USDT 本位永续合约，覆盖约 ${volumeHistory.data.coveragePct}% 合约成交额 · ${volumeHistory.data.startDate} 起` : ""}{volumeHistory?.state === "cached" ? " · 已显示缓存" : ""}</p>
        <p className="marketOverviewScope">此口径仅覆盖所选永续合约，不含现货与期权，与官方全平台 24h 总额不同，不代表全加密市场成交额。</p>
      </Paper>

      <Paper component="section" className="marketOverviewPanel marketOverviewEvents" withBorder shadow="none" aria-label="近期美国事件" aria-busy={eventsLoading}>
        <div className="marketOverviewPanelHeader"><div><h2>近期美国事件</h2><p>过去 7 天与未来 31 天 · 上海时间</p></div><Button type="button" size="xs" variant="subtle" onClick={onOpenEvents}>完整日历</Button></div>
        {!events && eventsLoading ? <DataLoadingSkeleton label="正在读取美国事件" /> : overviewEvents.length ? <div className="marketOverviewEventList">{overviewEvents.map(({ event, upcoming }) => <div className={`marketOverviewEvent${upcoming ? "" : " isPast"}`} key={event.id}><time>{overviewShanghaiTime(event.scheduledAt)}</time><strong title={`官方名称：${event.title}`}>{usEventDisplayTitle(event)}</strong><span>{usEventProviderLabel(event.provider)} · {upcoming ? overviewEventRelativeTime(event.scheduledAt ?? 0) : "已公布"}</span></div>)}</div> : <EmptyState compact>{eventsError ? "美国事件暂不可用。" : events?.refreshing ? "官方日历正在后台同步，完成后自动显示。" : "近期暂无已公布的官方事件。"}</EmptyState>}
        {eventsError ? <Notice tone={events?.data?.length ? "warning" : "danger"}>{eventsError}</Notice> : null}
        {eventsLoading && events ? <span className="marketOverviewUpdating" role="status">日历更新中</span> : null}
        <p className="marketOverviewSource">来源：美国官方事件日历{eventProviders.length ? ` · ${healthyProviders}/${eventProviders.length} 个来源正常` : ""}{events?.cacheAgeMs ? ` · 缓存约 ${formatDuration(events.cacheAgeMs)}` : ""}</p>
      </Paper>

      <Paper component="section" className="marketOverviewPanel marketOverviewTickers" withBorder shadow="none" aria-label="代表合约行情" aria-busy={tickerLoading}>
        <div className="marketOverviewPanelHeader"><div><h2>代表合约行情</h2><p>OKX USDT 永续合约 · 最近 24 小时</p></div>{tickerLoading && tickers?.data?.length ? <span className="marketOverviewUpdating" role="status">更新中</span> : null}</div>
        {!tickers && tickerLoading ? <DataLoadingSkeleton label="正在读取代表合约行情" variant="metrics" /> : featured.length ? <div className="marketOverviewTickerList">{featured.map(({ instId, ticker }) => { const change = tickerRolling24hChange(ticker).percent; const turnover = instrumentQuoteTurnover(ticker); return <UnstyledButton key={instId} type="button" className="marketOverviewTicker" onClick={() => onOpenChart(instId)} aria-label={`查看 ${instId} 行情图表`} title={`${instId} · 24h 高 ${formatMarketNumber(ticker?.high24h)} / 低 ${formatMarketNumber(ticker?.low24h)} · 成交额按最新价折算`}><span><strong>{instId.split("-")[0]}</strong><small>{instId}</small></span><span><strong>{formatMarketNumber(ticker?.last)} USDT</strong><small>最新价</small></span><span className={changeClass(change)}><strong>{formatSignedPercent(change)}</strong><small>24h 涨跌</small></span><span><strong>{turnover === null ? "--" : formatCompact(turnover)} USDT</strong><small>24h 成交额（估算）</small></span></UnstyledButton>; })}</div> : <EmptyState compact>{tickers?.refresh?.state === "initializing" ? "行情列表正在获取完整快照。" : "代表合约行情暂不可用。"}</EmptyState>}
        {featured.length > 0 && featured.length < OVERVIEW_CONTRACTS.length ? <Notice>部分代表合约暂无行情。</Notice> : null}
        {tickerStale ? <Notice>合约行情暂时使用最近快照。</Notice> : null}
        {tickerError ? <Notice tone={featured.length ? "warning" : "danger"}>{tickerError}</Notice> : null}
        <p className="marketOverviewSource">来源：OKX 永续合约 ticker · 更新于 {overviewShanghaiTime(tickers?.ts)}（上海时间）</p>
      </Paper>

      <Paper component="section" className="marketOverviewPanel marketOverviewBreadth" withBorder shadow="none" aria-label="市场宽度" aria-busy={tickerLoading}>
        <div className="marketOverviewPanelHeader">
          <div><h2>市场宽度</h2><p>OKX 永续合约 · 全量 {breadth.total} 个</p></div>
          {breadth.total ? <span className={`marketOverviewSentiment${breadth.sentiment === "普涨" ? " isUp" : breadth.sentiment === "普跌" ? " isDown" : ""}`}>{breadth.sentiment}</span> : null}
        </div>
        {!tickers && tickerLoading ? <DataLoadingSkeleton label="正在统计全市场涨跌" variant="metrics" /> : breadth.total ? <>
          <div className="marketOverviewBreadthCounts">
            <span className="up"><strong>{breadth.up}</strong><small>上涨</small></span>
            <span className="down"><strong>{breadth.down}</strong><small>下跌</small></span>
            <span><strong>{breadth.flat}</strong><small>平盘</small></span>
          </div>
          <div className="marketOverviewBreadthBar" role="img" aria-label={`上涨 ${breadth.up} 个，下跌 ${breadth.down} 个，平盘 ${breadth.flat} 个`}>
            <span className="up" style={{ width: `${(breadth.up / breadth.total) * 100}%` }} />
            <span className="down" style={{ width: `${(breadth.down / breadth.total) * 100}%` }} />
            <span className="flat" style={{ width: `${(breadth.flat / breadth.total) * 100}%` }} />
          </div>
          <div className="marketOverviewBreadthMetrics">
            <span><strong>{formatSignedPercent(breadth.medianChange)}</strong><small>涨跌幅中位数</small></span>
            <span><strong>{formatSignedPercent(breadth.averageChange)}</strong><small>平均涨跌幅</small></span>
            <span><strong>{breadth.turnoverUsd === null ? "--" : formatCompact(breadth.turnoverUsd)} USD</strong><small>24h 成交额（估算）</small></span>
          </div>
          <div className="marketOverviewBreadthLeaders">
            <div><h3>领涨</h3>{breadth.gainers.length ? breadth.gainers.map((item) => <UnstyledButton key={item.instId} type="button" className="marketOverviewLeader" onClick={() => onOpenChart(item.instId)} aria-label={`查看 ${item.instId} 行情图表`}><span>{item.instId.split("-")[0]}</span><strong className={changeClass(item.change)}>{formatSignedPercent(item.change)}</strong></UnstyledButton>) : <p>暂无上涨合约</p>}</div>
            <div><h3>领跌</h3>{breadth.losers.length ? breadth.losers.map((item) => <UnstyledButton key={item.instId} type="button" className="marketOverviewLeader" onClick={() => onOpenChart(item.instId)} aria-label={`查看 ${item.instId} 行情图表`}><span>{item.instId.split("-")[0]}</span><strong className={changeClass(item.change)}>{formatSignedPercent(item.change)}</strong></UnstyledButton>) : <p>暂无下跌合约</p>}</div>
          </div>
        </> : <EmptyState compact>市场宽度暂不可用。</EmptyState>}
        <p className="marketOverviewSource">来源：OKX 永续合约 ticker · 按 24h 开盘价计算涨跌 · 成交额按最新价折算</p>
      </Paper>
    </div>
  </section>;
}

function UsMarketTimelinePage({ date, onDateChange }: { date: string; onDateChange: (value: string) => void }) {
  const [events, setEvents] = React.useState<UsMarketEvent[]>([]);
  const [warnings, setWarnings] = React.useState<string[]>([]);
  const [providerStatuses, setProviderStatuses] = React.useState<UsMarketProviderStatus[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const [refreshNonce, setRefreshNonce] = React.useState(0);
  const [error, setError] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [state, setState] = React.useState("");
  const focusWindow = React.useMemo(() => timelineFocusWindow(date), [date]);
  const dates = React.useMemo(() => Array.from({ length: 7 }, (_, index) => {
    return shiftTimelineDate(date, index - 3);
  }), [date]);
  React.useEffect(() => {
    let active = true; let refreshTimer = 0; setLoading(!events.length); setError("");
    const query = new URLSearchParams({ from: focusWindow.from, to: focusWindow.to }); if (category) query.set("categories", category); if (state) query.set("states", state);
    fetch(`${API_BASE}/api/market/us-events?${query}`).then(async (response) => {
      if (!response.ok) throw new Error(String((await response.json().catch(() => ({}))).detail || "美国事件加载失败"));
      return response.json() as Promise<UsMarketEventsResponse>;
    }).then((payload) => { if (active) { setEvents(payload.data ?? []); setWarnings(payload.warnings ?? []); setProviderStatuses(payload.providerStatuses ?? []); setRefreshing(Boolean(payload.refreshing)); refreshTimer = window.setTimeout(() => setRefreshNonce((value) => value + 1), payload.refreshing ? 3_000 : 30_000); } }).catch((reason) => active && setError(reason instanceof Error ? reason.message : "美国事件加载失败")).finally(() => active && setLoading(false));
    return () => { active = false; if (refreshTimer) window.clearTimeout(refreshTimer); };
  }, [category, events.length, focusWindow.from, focusWindow.to, refreshNonce, state]);
  const isHistoricalUnverified = (event: UsMarketEvent) => event.state === "scheduled" && Boolean(event.scheduledAt && event.scheduledAt < Date.now());
  const label = (event: UsMarketEvent) => event.state === "released" ? "已公布" : event.state === "revised" ? "已修正" : event.state === "cancelled" ? "已取消" : isHistoricalUnverified(event) ? "历史值待核验" : "预告";
  const eventDay = (event: UsMarketEvent) => event.scheduledAt ? shanghaiDate(new Date(event.scheduledAt)) : "";
  const eventTime = (event: UsMarketEvent) => !event.timeKnown || !event.scheduledAt ? "待确认" : new Date(event.scheduledAt).toLocaleTimeString("zh-CN", { timeZone: "Asia/Shanghai", hour: "2-digit", minute: "2-digit" });
  const isPolicyDecision = (event: UsMarketEvent) => event.provider === "Federal Reserve" && /会议与利率决议|政策声明与利率决定|利率决策/.test(event.title);
  const isPolicyBundleDuplicate = (event: UsMarketEvent) => isPolicyDecision(event) || (event.provider === "Federal Reserve" && event.title === "FOMC 会议（美国）");
  const groupedEvents = React.useMemo(() => {
    const groups = new Map<string, UsMarketEvent[]>();
    events.forEach((event) => { const day = eventDay(event); if (day) groups.set(day, [...(groups.get(day) ?? []), event]); });
    return [...groups.entries()].map(([day, dayEvents]) => {
      const decision = dayEvents.find((event) => event.title.includes("美联储利率决策")) ?? dayEvents.find(isPolicyDecision);
      const visible = decision ? dayEvents.filter((event) => event === decision || !isPolicyBundleDuplicate(event)) : dayEvents;
      return [day, visible] as [string, UsMarketEvent[]];
    });
  }, [events]);
  const freshProviders = providerStatuses.filter((item) => item.status === "fresh").length;
  const attentionProviders = providerStatuses.length - freshProviders;
  const unavailableProviders = providerStatuses.filter((item) => item.status !== "fresh");
  const today = shanghaiDate(new Date());
  const figuresFor = (event: UsMarketEvent) => [
    event.actual ? ["公布", event.actual] : null,
    event.previousValue ? ["前值", event.previousValue] : null,
    event.forecast ? ["预期", event.forecast] : null,
  ].filter((item): item is [string, string] => Boolean(item));
  const policyFacts = (event: UsMarketEvent) => [
    ["公布", event.actual || "--"],
    ["前值", event.previousValue || "--"],
    ["预期", event.forecast || "暂无已验证预期"],
  ];
  return <section className="marketMain usTimelinePage" aria-label="美国事件时间轴">
    <div className="usTimelineHeader" aria-label="日期导航">
      <ActionIcon type="button" className="iconButton" aria-label="上个月" onClick={() => onDateChange(shiftTimelineMonth(date, -1))} variant="subtle"><ChevronLeft size={22} /></ActionIcon>
      <DateInput className="usTimelineDateControl" aria-label="选择日期" value={date} onChange={(value) => value && onDateChange(value)} valueFormat="YYYY-MM-DD" size="sm" popoverProps={{ position: "bottom-start" }} />
      <ActionIcon type="button" className="iconButton" aria-label="下个月" onClick={() => onDateChange(shiftTimelineMonth(date, 1))} variant="subtle"><ChevronRight size={22} /></ActionIcon>
      <Button type="button" className="usTimelineNow" aria-label="回到今天" title="回到今天" onClick={() => onDateChange(today)} disabled={date === today} variant="default" size="xs">今天</Button>
    </div>
    <div className="usTimelineDates">
      {dates.map((item) => (
        <UnstyledButton key={item} type="button" className={item === date ? "selected" : ""} aria-pressed={item === date} onClick={() => onDateChange(item)}>
          <strong>{item.slice(-2)}</strong>
          <span>{new Date(`${item}T00:00:00+08:00`).toLocaleDateString("zh-CN", { weekday: "short", timeZone: "Asia/Shanghai" })}</span>
        </UnstyledButton>
      ))}
    </div>
    <div className="usTimelineFilters">
      <SegmentedControl className="usTimelineFilterGroup" aria-label="事件分类" value={category} onChange={setCategory} data={US_TIMELINE_CATEGORIES.map(([value, label]) => ({ value, label }))} size="xs" />
      <Popover position="bottom-start" shadow="sm" withArrow>
        <Popover.Target><Button type="button" variant="subtle" size="xs">状态筛选</Button></Popover.Target>
        <Popover.Dropdown><SegmentedControl className="usTimelineFilterGroup" aria-label="事件状态" value={state} onChange={setState} data={US_TIMELINE_STATES.map(([value, label]) => ({ value, label }))} size="xs" /></Popover.Dropdown>
      </Popover>
    </div>
    {error ? <Notice tone="danger">{error}</Notice> : null}
    {loading && !events.length ? <DataLoadingSkeleton label="正在读取已保存日历" /> : groupedEvents.length ? <div className="usTimelineList">{groupedEvents.map(([day, dayEvents]) => <section className={`usTimelineDay ${day === date ? "focused" : ""}`} key={day}><h2 className="usTimelineDateTitle">{day.replace(/-/g, "/")}</h2>{dayEvents.map((event) => { const primary = isPolicyDecision(event); const figures = primary ? policyFacts(event) : figuresFor(event); const historicalUnverified = isHistoricalUnverified(event); return <article className={`usEventCard ${primary ? "primary" : "compact"}`} key={event.id}><time>{eventTime(event)}{event.timeKnown ? <small>上海时间</small> : null}</time><div><div className="usEventTitle"><strong>{usEventDisplayTitle(event)}</strong><span className={`usEventState ${event.state} ${historicalUnverified ? "historical" : ""}`}>{label(event)}</span><a className="usEventSource" href={event.sourceUrl} target="_blank" rel="noreferrer" aria-label={`${usEventDisplayTitle(event)} 的官方来源，${event.sourceTimezone || "America/New_York"}`} title={`官方来源 · ${event.sourceTimezone || "America/New_York"}`}><ExternalLink size={14} /></a></div>{primary ? <div className="usEventValues policyFacts">{figures.map(([name, value]) => <span key={name}>{name}<b>{value}</b></span>)}</div> : figures.length ? <div className={`usEventValues count-${figures.length}`}>{figures.map(([name, value]) => <span key={name}>{name}<b>{value}</b></span>)}</div> : historicalUnverified ? <p className="usEventHistoricalPending">该历史日程尚无可核验的官方数值，保留日程与来源，不填充猜测数据。</p> : null}{(event.period_label || event.unit || event.revision) && <p className="usEventContext">{[event.period_label, event.unit, event.revision ? `修订：${event.revision}` : ""].filter(Boolean).join(" · ")}</p>}</div></article>; })}</section>)}</div> : <EmptyState>{refreshing ? "正在同步该日期窗口的官方日历…" : "所选日期附近暂无符合筛选条件的官方事件。"}</EmptyState>}
    {refreshing && groupedEvents.length ? <DataLoadingState label="已显示缓存，官方日历正在后台更新" compact /> : null}
    {attentionProviders ? <Disclosure className="usTimelineSourceWarning" label={<><AlertTriangle size={14} />数据状态</>}><span>{unavailableProviders.map((item) => usEventProviderLabel(item.provider)).join("、")} 暂时使用已保存日历或不可用；已显示可读取的官方事件。</span></Disclosure> : providerStatuses.length ? null : warnings.map((warning) => <Notice key={warning} tone="warning">{warning}</Notice>)}
  </section>;
}

function AnnouncementsPage() {
  const [typesPayload, setTypesPayload] = React.useState<AnnouncementTypesResponse | null>(null);
  const [payload, setPayload] = React.useState<AnnouncementsResponse | null>(null);
  const [selectedType, setSelectedType] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [loading, setLoading] = React.useState(false);
  const [typesLoading, setTypesLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [typesError, setTypesError] = React.useState("");
  const [reloadNonce, setReloadNonce] = React.useState(0);
  const forceReloadRef = React.useRef(false);

  React.useEffect(() => {
    let active = true;
    setTypesLoading(true);
    setTypesError("");
    fetch(`${API_BASE}/api/announcements/types`)
      .then(async (response) => {
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail ?? "公告分类加载失败");
        }
        return response.json();
      })
      .then((nextPayload: AnnouncementTypesResponse) => {
        if (!active) return;
        setTypesPayload(nextPayload);
      })
      .catch((nextError) => {
        if (!active) return;
        setTypesError(nextError instanceof Error ? nextError.message : "公告分类加载失败");
      })
      .finally(() => {
        if (active) setTypesLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  React.useEffect(() => {
    let active = true;
    const force = forceReloadRef.current;
    forceReloadRef.current = false;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ page: String(page), language: "zh-CN" });
    if (selectedType) params.set("annType", selectedType);
    if (force) params.set("force", "true");
    fetch(`${API_BASE}/api/announcements?${params.toString()}`)
      .then(async (response) => {
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail ?? "公告加载失败");
        }
        return response.json();
      })
      .then((nextPayload: AnnouncementsResponse) => {
        if (!active) return;
        setPayload(nextPayload);
      })
      .catch((nextError) => {
        if (!active) return;
        setError(nextError instanceof Error ? nextError.message : "公告加载失败");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, reloadNonce, selectedType]);

  const typeOptions = React.useMemo(() => [{ annType: "", annTypeDesc: "全部公告" }, ...(typesPayload?.data ?? [])], [typesPayload]);
  const totalPage = Math.max(1, payload?.totalPage ?? 1);
  const rows = payload?.data ?? [];
  const warning = error || payload?.warning || typesError || typesPayload?.warning || "";
  const sourceText = sourceLabel(payload?.source ?? typesPayload?.source);
  const updatedText = payload?.ts ? formatTime(payload.ts) : "--";
  const cacheText = formatDuration(payload?.cacheAgeMs ?? typesPayload?.cacheAgeMs);

  const refresh = () => {
    forceReloadRef.current = true;
    setReloadNonce((value) => value + 1);
  };

  const chooseType = (annType: string) => {
    setSelectedType(annType);
    setPage(1);
  };

  return (
    <section className="announcementsPage">
      <PageHeader title="OKX 公告" description={`${announcementTypeLabel(typesPayload?.data ?? [], selectedType)} · ${sourceText} · 更新 ${updatedText} · 缓存 ${cacheText}`} actions={
        <div className="workspaceActions">
          <Badge className={`statusPill ${warning ? "warning" : "live"}`} color={warning ? "yellow" : "teal"} variant="light">{loading || typesLoading ? "加载中" : sourceText}</Badge>
          <Button type="button" className="secondaryButton slim" onClick={refresh} disabled={loading} variant="default" size="xs" leftSection={<RefreshCw size={15} />}>
            {loading ? "刷新中" : "刷新"}
          </Button>
        </div>
      } />

      {warning ? (
        <div className="radarFeedback">
          <Notice tone={error ? "danger" : "warning"}>{warning}</Notice>
        </div>
      ) : null}

      <div className="announcementLayout">
        <Paper component="aside" className="announcementTypePanel" p={0} aria-label="公告分类">
          <div className="panelHeader">
            <div>
              <Megaphone size={16} />
              <strong>分类</strong>
            </div>
            <span>{typesLoading ? "加载中" : `${Math.max(0, typeOptions.length - 1)} 类`}</span>
          </div>
          <div className="announcementTypeList">
            {typesLoading && !typesPayload ? <DataLoadingSkeleton label="正在读取公告分类" /> : typeOptions.map((item) => (
              <UnstyledButton
                key={item.annType || "all"}
                type="button"
                className={selectedType === item.annType ? "selected" : ""}
                onClick={() => chooseType(item.annType)}
                title={item.annType ? `${item.annTypeDesc} (${item.annType})` : item.annTypeDesc}
              >
                <span>{item.annTypeDesc}</span>
              </UnstyledButton>
            ))}
          </div>
        </Paper>

        <Paper component="section" className="announcementListPanel" p={0} aria-label="公告列表">
          <div className="announcementListHeader">
            <div>
              <strong>{announcementTypeLabel(typesPayload?.data ?? [], selectedType)}</strong>
              <span>{loading && !payload ? "正在加载公告" : `${rows.length} 条 · 第 ${page}/${totalPage} 页`}</span>
            </div>
            <div className="announcementPager">
              <Button type="button" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={loading || page <= 1} variant="default" size="xs">
                上一页
              </Button>
              <span>{page}/{totalPage}</span>
              <Button type="button" onClick={() => setPage((value) => Math.min(totalPage, value + 1))} disabled={loading || page >= totalPage} variant="default" size="xs">
                下一页
              </Button>
            </div>
          </div>

          <div className="announcementRows">
            {loading && !payload ? <DataLoadingSkeleton label="正在读取公告列表" /> : rows.length ? (
              rows.map((item) => (
                <article className="announcementRow" key={`${item.annType}-${item.pTime}-${item.url}`}>
                  <div className="announcementTitleBlock">
                    <strong>{item.title}</strong>
                    <span>{announcementTypeLabel(typesPayload?.data ?? [], item.annType)}</span>
                  </div>
                  <div className="announcementTimes">
                    <span>展示 {formatTime(item.businessPTime)}</span>
                    <span>首次 {formatTime(item.pTime)}</span>
                  </div>
                  <a className="announcementLink" href={item.url} target="_blank" rel="noreferrer">
                    <ExternalLink size={14} />
                    原文
                  </a>
                </article>
              ))
            ) : (
              <div className="emptyState">{loading ? "公告加载中" : "暂无公告"}</div>
            )}
          </div>
          {loading && payload ? <DataLoadingState label="公告列表更新中，已保留当前内容" compact /> : null}
        </Paper>
      </div>
    </section>
  );
}

function RadarFlowSnapshot({ stats }: { stats: MarketStatsModel }) {
  const accountShares = longShortAccountShares(stats.longShortStats?.latest);
  const buyShare = toNumber(stats.takerVolumeStats?.buySharePct);
  const sellShare = buyShare === null ? null : Math.max(0, 100 - buyShare);
  const initialLoading = stats.marketStatsLoading && !stats.marketStats;
  const hasAccountRatio = accountShares.longPct !== null && accountShares.shortPct !== null;
  const hasTakerVolume = Boolean(stats.takerVolumeStats?.buyVol || stats.takerVolumeStats?.sellVol);
  const visibleWarnings = Array.from(new Set(stats.statsWarnings)).filter((warning) =>
    /多空人数比|主动买卖量|交易统计/.test(warning)
  );
  const hasMissingVisibleData = !hasAccountRatio || !hasTakerVolume;
  const flowStatus = initialLoading
    ? "加载中"
    : stats.marketStatsLoading
      ? "更新中"
      : !hasAccountRatio && !hasTakerVolume
        ? "数据暂不可用"
        : hasMissingVisibleData
          ? "部分数据待补齐"
          : visibleWarnings.length
            ? "已显示上次数据"
            : `更新 ${stats.statsUpdatedAt}`;

  return (
    <section className="radarFlowSnapshot" aria-label="当前多空账户与主动成交" aria-busy={stats.marketStatsLoading}>
      <div className="radarFlowHeader">
        <div>
          <strong>多空与主动成交</strong>
          <span>{stats.displayedStatsPeriod} 最新区间</span>
        </div>
        <span className={hasMissingVisibleData || visibleWarnings.length ? "warning" : ""} aria-live="polite">
          {flowStatus}
        </span>
      </div>

      {initialLoading ? (
        <div className="radarFlowLoading" role="status">
          <span className="dataLoadingSpinner" aria-hidden="true" />
          正在读取多空与主动成交数据
        </div>
      ) : (
        <div className="radarFlowGrid">
          <div className="radarFlowRow">
            <span className="radarFlowLabel">账户比例</span>
            <div className="radarFlowValues">
              <span className="radarFlowLong"><small>多头账户</small><strong>{formatStatsShare(accountShares.longPct)}</strong></span>
              <span className="radarFlowShort"><small>空头账户</small><strong>{formatStatsShare(accountShares.shortPct)}</strong></span>
            </div>
            <div className="radarFlowBar" aria-hidden="true">
              <span className="long" style={{ width: `${accountShares.longPct ?? 0}%` }} />
              <span className="short" style={{ width: `${accountShares.shortPct ?? 0}%` }} />
            </div>
            {!hasAccountRatio ? <small className="radarFlowUnavailable">暂无多空账户比例</small> : null}
          </div>

          <div className="radarFlowRow">
            <span className="radarFlowLabel">主动成交量</span>
            <div className="radarFlowValues">
              <span className="radarFlowLong">
                <small>主动买入 · {formatStatsShare(buyShare)}</small>
                <strong>{formatStatsCompact(stats.takerVolumeStats?.buyVol, stats.takerVolumeStats?.unit)}</strong>
              </span>
              <span className="radarFlowShort">
                <small>主动卖出 · {formatStatsShare(sellShare)}</small>
                <strong>{formatStatsCompact(stats.takerVolumeStats?.sellVol, stats.takerVolumeStats?.unit)}</strong>
              </span>
            </div>
            <div className="radarFlowBar" aria-hidden="true">
              <span className="long" style={{ width: `${buyShare ?? 0}%` }} />
              <span className="short" style={{ width: `${sellShare ?? 0}%` }} />
            </div>
            {!hasTakerVolume ? <small className="radarFlowUnavailable">暂无主动成交量</small> : null}
          </div>
        </div>
      )}

      <p className="radarFlowNote">账户多空与主动成交是两套独立口径，不等同于开多、开空成交量。</p>
    </section>
  );
}

function ContractRadarPage({ onOpenContract }: { onOpenContract: (instId: string, target: RadarActionTarget) => void }) {
  const [settlement, setSettlement] = React.useState("usdt");
  const [minVolume, setMinVolume] = React.useState("1000000");
  const [volatility, setVolatility] = React.useState("all");
  const [risk, setRisk] = React.useState("all");
  const [sortBy, setSortBy] = React.useState<RadarSortKey>("turnover_1h");
  const [resultVolatility, setResultVolatility] = React.useState("all");
  const [resultMinTurnover, setResultMinTurnover] = React.useState("");
  const [resultFiltersExpanded, setResultFiltersExpanded] = React.useState(false);
  const [payload, setPayload] = React.useState<RadarResponse | null>(null);
  const [analysis, setAnalysis] = React.useState<RadarMarketAnalysis | null>(null);
  const [selectedInstId, setSelectedInstId] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [analysisLoading, setAnalysisLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [analysisError, setAnalysisError] = React.useState("");
  const radarListRef = React.useRef<HTMLDivElement | null>(null);

  const resultMinimumTurnover = React.useMemo(
    () => radarResultMinimumTurnover(resultMinTurnover),
    [resultMinTurnover]
  );
  const hasResultFilters = resultVolatility !== "all" || resultMinimumTurnover > 0;
  const visibleRadarResults = React.useMemo(() => (
    (payload?.data ?? []).filter((item) => (
      (resultVolatility === "all" || item.volatilityLevel === resultVolatility) &&
      (resultMinimumTurnover === 0 || (radarComparableTurnoverValue(item) ?? 0) >= resultMinimumTurnover)
    ))
  ), [payload?.data, resultMinimumTurnover, resultVolatility]);
  const clearResultFilters = React.useCallback(() => {
    setResultVolatility("all");
    setResultMinTurnover("");
    setResultFiltersExpanded(false);
  }, []);

  const selectedResult = React.useMemo(
    () => visibleRadarResults.find((item) => item.instId === selectedInstId) ?? visibleRadarResults[0] ?? null,
    [selectedInstId, visibleRadarResults]
  );
  const radarFlowStats = useMarketStats(selectedResult?.instId ?? "", selectedResult?.bar ?? "15m");

  const radarParams = React.useCallback(
    (force = false, sortOverride = sortBy) =>
      new URLSearchParams({
        settlement,
        minVolume: minVolume.trim() || "1000000",
        volatility,
        risk,
        limit: "30",
        candidateLimit: "60",
        bar: "15m",
        sortBy: sortOverride,
        explain: "false",
        force: String(force)
      }),
    [minVolume, risk, settlement, sortBy, volatility]
  );

  const loadRadar = React.useCallback(
    async (force = false, sortOverride = sortBy) => {
      setLoading(true);
      setError("");
      setAnalysis(null);
      setAnalysisError("");
      const previousSort = payload?.sort?.key;
      const params = radarParams(force, sortOverride);
      try {
        const response = await fetch(`${API_BASE}/api/market/radar?${params.toString()}`);
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail ?? "合约雷达扫描失败");
        }
        const nextPayload: RadarResponse = await response.json();
        setPayload(nextPayload);
        if (nextPayload.sort?.key === "turnover_1h" || nextPayload.sort?.key === "turnover_24h") {
          setSortBy(nextPayload.sort.key);
        }
        setSelectedInstId((current) =>
          current && nextPayload.data.some((item) => item.instId === current) ? current : nextPayload.data[0]?.instId ?? ""
        );
        window.requestAnimationFrame(() => {
          if (radarListRef.current) radarListRef.current.scrollTop = 0;
        });
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : "合约雷达扫描失败");
        if (previousSort === "turnover_1h" || previousSort === "turnover_24h") {
          setSortBy(previousSort);
        }
      } finally {
        setLoading(false);
      }
    },
    [payload?.sort?.key, radarParams, sortBy]
  );

  const selectRadarSort = React.useCallback(
    (nextSort: RadarSortKey) => {
      if (nextSort === sortBy) return;
      if (!payload) {
        setSortBy(nextSort);
        return;
      }
      const ranking = payload.rankings?.[nextSort];
      if (!ranking) {
        setError("当前雷达快照不支持双口径本地切换，请重新扫描。");
        return;
      }
      setError("");
      setAnalysis(null);
      setAnalysisError("");
      setSortBy(nextSort);
      setPayload((current) => {
        if (!current) return current;
        const nextRanking = current.rankings?.[nextSort];
        if (!nextRanking) return current;
        return {
          ...current,
          data: nextRanking,
          filters: { ...current.filters, sortBy: nextSort },
          sort: { ...current.sort, key: nextSort, label: radarSortLabel(nextSort), legacy: false },
          summary: current.summary ? { ...current.summary, returned: nextRanking.length } : current.summary
        };
      });
      setSelectedInstId((current) => ranking.some((item) => item.instId === current) ? current : ranking[0]?.instId ?? "");
      window.requestAnimationFrame(() => {
        if (radarListRef.current) radarListRef.current.scrollTop = 0;
      });
    },
    [payload, sortBy]
  );

  const loadAnalysis = React.useCallback(
    async (force = false) => {
      if (!payload) return;
      setAnalysisLoading(true);
      setAnalysisError("");
      const params = radarParams(false);
      params.delete("explain");
      params.set("force", String(force));
      try {
        const response = await fetch(`${API_BASE}/api/market/radar/analysis?${params.toString()}`);
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail ?? "AI 大盘分析失败");
        }
        const nextAnalysis: RadarMarketAnalysis = await response.json();
        setAnalysis(nextAnalysis);
      } catch (nextError) {
        setAnalysisError(nextError instanceof Error ? nextError.message : "AI 大盘分析失败");
      } finally {
        setAnalysisLoading(false);
      }
    },
    [payload, radarParams]
  );

  const summary = payload?.summary;
  const activeSort = payload?.sort?.key === "turnover_1h" || payload?.sort?.key === "turnover_24h" ? payload.sort.key : sortBy;
  const activeSortLabel = payload?.sort?.label || radarSortLabel(activeSort);
  const appliedFilters = payload?.filters;
  const hasPendingScanFilters = Boolean(
    payload && appliedFilters && (
      String(appliedFilters.settlement || "").toLowerCase() !== settlement ||
      String(appliedFilters.minVolume || "") !== (minVolume.trim() || "1000000") ||
      String(appliedFilters.volatility || "") !== volatility ||
      String(appliedFilters.risk || "") !== risk
    )
  );
  const analysisSource = analysis?.originSource || analysis?.source || "";
  const analysisNotConfigured = analysis?.status === "not-configured" || analysisSource === "llm-not-configured";
  const analysisFromLlm = analysisSource === "llm-market-analysis";
  const analysisTitle = analysisFromLlm ? "全市场 AI 观察" : "全市场指标分析 · 规则降级";
  const setupGuide = analysis?.setupGuide;
  const warning = error || radarWarningText(payload?.warning) || "";
  const updatedLabel = payload?.ts ? new Date(payload.ts).toLocaleTimeString("zh-CN") : "--";
  const scanButtonLabel = loading ? "扫描中" : payload ? "重新扫描" : "开始扫描";
  const analysisButtonLabel = analysisLoading ? "分析中" : analysisNotConfigured ? "重新检测" : analysis ? "刷新 AI" : "AI 分析";
  const radarStatusText = loading && !payload
    ? "正在扫描合约 · 正在筛选候选与 K线数据"
    : payload
    ? loading
      ? `正在按 ${radarSortLabel(sortBy)} 更新 · 当前仍显示 ${activeSortLabel} 结果`
      : `${activeSortLabel} · ${sourceLabel(payload.source)} · ${summary ? `${summary.returned}/${summary.candidates}/${summary.total}` : "--"} · ${updatedLabel}${hasPendingScanFilters ? " · 筛选条件已变更，点击重新扫描后生效" : ""}`
    : "未扫描";
  const compactHighlights = analysis?.highlights.slice(0, 2) ?? [];
  const displayWatchlist = React.useMemo(() => {
    type WatchItem = {
      instId: string;
      direction?: string;
      entryZone?: string;
      isSelected: boolean;
      selectedNote: string;
    };
    const base: WatchItem[] = (analysis?.watchlist ?? []).slice(0, 3).map((item) => ({
      instId: item.instId,
      direction: item.direction,
      entryZone: item.entryZone,
      isSelected: false,
      selectedNote: "",
    }));
    const currentId = (selectedResult?.instId ?? "").toUpperCase();
    if (!currentId) return base;
    const hit = base.find((item) => item.instId.toUpperCase() === currentId);
    if (hit) {
      // Already picked by the AI: move it to the top, keep AI direction/price.
      return [
        { ...hit, isSelected: true, selectedNote: "当前选中" },
        ...base.filter((item) => item.instId.toUpperCase() !== currentId),
      ];
    }
    // Not in the AI list: add a labelled row using only the existing rule baseline.
    return [
      {
        instId: selectedResult?.instId ?? "",
        direction: selectedResult?.direction,
        entryZone: selectedResult?.entryZone || "",
        isSelected: true,
        selectedNote: "当前选中 · 指标参考",
      },
      ...base,
    ];
  }, [analysis?.watchlist, selectedResult]);
  const compactRisks = analysis ? [...analysis.riskWarnings, ...analysis.suggestedFilters].slice(0, 2) : [];
  const compactAnalysisWarning = analysis?.warnings?.[0] ?? "";
  const sentimentView = radarSentimentView(analysis?.marketSummary?.sentiment);
  const analysisBias = radarBiasView(analysis?.marketBias);
  const fundingData = analysis?.marketSummary?.sentiment?.funding;
  const fundingSampled = Number(fundingData?.sampled ?? 0);
  const bullPct = fundingSampled ? Math.round((Number(fundingData?.positive ?? 0) / fundingSampled) * 100) : 0;
  const bearPct = fundingSampled ? Math.round((Number(fundingData?.negative ?? 0) / fundingSampled) * 100) : 0;
  const neuPct = Math.max(0, 100 - bullPct - bearPct);

  return (
    <section className="radarPage radarPageCompact">
      <div className="radarCompactHeader">
        <div className="radarCompactTitle">
          <span className="eyebrow">合约雷达</span>
          <strong>选合约</strong>
        </div>
        <div className="radarMetaLine" aria-label="雷达状态" aria-live="polite">
          <span>可玩优先</span>
          <span>{radarStatusText}</span>
          {analysisNotConfigured ? <span>LLM 未配置</span> : analysis ? <span>{analysisFromLlm ? "AI" : "指标"} {radarMarketRegimeLabel(analysis.marketRegime)}</span> : null}
          {analysis?.marketBias && !analysisNotConfigured ? <span className={`radarBiasTag ${analysisBias.tone}`}>{analysisBias.label}</span> : null}
        </div>
      </div>

      {warning ? <Notice tone={error ? "danger" : "warning"}>{warning}</Notice> : null}

      <Paper component="section" className="radarControls">
        <div className="filterGroup">
          <span>结算</span>
          <SegmentedControl aria-label="结算方式" value={settlement} onChange={setSettlement} data={[{ value: "usdt", label: "USDT" }, { value: "coin", label: "币本位" }, { value: "all", label: "全部" }]} size="xs" />
        </div>
        <TextInput className="radarInput" label="扫描最小 24h 量" aria-label="下次扫描的最小24小时成交额" value={minVolume} onChange={(event) => setMinVolume(event.target.value)} inputMode="decimal" size="xs" />
        <div className="filterGroup radarSortGroup" aria-label="候选排行方式">
          <span>排行</span>
          <SegmentedControl aria-label="候选排行方式" value={sortBy} onChange={(value) => selectRadarSort(value as RadarSortKey)} data={[{ value: "turnover_1h", label: "1小时成交额" }, { value: "turnover_24h", label: "24小时成交额" }]} disabled={loading} size="xs" />
        </div>
        <Select className="radarInput" label="波动" value={volatility} onChange={(value) => setVolatility(value ?? "all")} data={[{ value: "all", label: "全部" }, { value: "high", label: "高波动" }, { value: "medium", label: "中波动" }, { value: "low", label: "低波动" }]} allowDeselect={false} size="xs" />
        <Select className="radarInput" label="风险提醒" value={risk} onChange={(value) => setRisk(value ?? "all")} data={[{ value: "all", label: "全部" }, { value: "low", label: "风险较低" }, { value: "medium", label: "需要注意" }, { value: "high", label: "风险较高" }]} allowDeselect={false} size="xs" />
        <Button className="primaryButton" type="button" onClick={() => loadRadar(true)} disabled={loading} size="xs" leftSection={<Search size={16} />}>
          {scanButtonLabel}
        </Button>
        <Button className="secondaryButton" type="button" onClick={() => loadAnalysis(Boolean(analysis))} disabled={!payload || loading || analysisLoading} aria-busy={analysisLoading} variant="default" size="xs" title="对全市场候选池生成 AI 观察，不针对单个选中合约" leftSection={<BrainCircuit size={16} className={analysisLoading ? "radarAnalysisSpinner isSpinning" : "radarAnalysisSpinner"} />}>
          {analysisButtonLabel}
        </Button>
      </Paper>

      {analysisLoading || analysisError || analysis ? (
        <Paper component="section" className={`radarAnalysisPanel ${analysisNotConfigured ? "setup" : analysis ? "ready" : "compactState"}`} aria-label={analysisNotConfigured ? "LLM 未配置" : analysisTitle}>
          {analysisLoading ? (
            <div className="radarBriefState radarBriefLoading" aria-live="polite">
              <Loader size={16} type="oval" aria-hidden="true" />
              <span className="radarBriefLoadingText">
                <strong>正在读取分析配置…</strong>
                <small>正在检查 LLM 配置与行情摘要，请稍候。</small>
              </span>
            </div>
          ) : analysisError ? (
            <Notice tone="danger">{analysisError}</Notice>
          ) : analysis ? (
            analysisNotConfigured ? (
              <div className="radarAnalysisSetup" role="status" aria-live="polite">
                <div className="radarSetupIcon"><BrainCircuit size={19} aria-hidden="true" /></div>
                <div className="radarSetupBody">
                  <span className="eyebrow">全市场 AI 观察未运行</span>
                  <strong>{setupGuide?.title ?? "尚未配置 LLM"}</strong>
                  <p>{setupGuide?.description ?? "未配置模型时不展示分析结果，请前往「设置 · AI 配置」完成配置。"}</p>
                  {(setupGuide?.steps ?? []).length ? (
                    <ol className="radarSetupSteps">
                      {(setupGuide?.steps ?? []).map((step, stepIndex) => <li key={stepIndex}>{step}</li>)}
                    </ol>
                  ) : null}
                  {setupGuide?.providerHint ? <p className="radarSetupHint">{setupGuide.providerHint}</p> : null}
                  <div className="radarSetupActions">
                    <Button className="primaryButton" type="button" size="xs" leftSection={<UserCog size={14} />} onClick={() => { window.location.hash = setupGuide?.settingsPath ?? "#/settings/llm"; }}>
                      前往 AI 配置
                    </Button>
                    <Button className="secondaryButton" type="button" size="xs" variant="default" leftSection={<RefreshCw size={14} />} onClick={() => loadAnalysis(true)} disabled={analysisLoading}>
                      重新检测
                    </Button>
                  </div>
                  <span className="radarSetupNote"><Info size={13} aria-hidden="true" />保存配置后无需重新扫描，点「重新检测」即可。</span>
                </div>
              </div>
            ) : (
            <>
              <div className="radarBriefHero">
                <span className="eyebrow">{analysisTitle}</span>
                <div className="radarBriefTitle">
                  <strong>{radarMarketRegimeLabel(analysis.marketRegime)}</strong>
                  {!analysisFromLlm ? <span className="radarAnalysisSourceTag">规则生成</span> : null}
                  {analysis.marketBias ? <span className={`radarBiasTag ${analysisBias.tone}`}>{analysisBias.label}</span> : null}
                  <span>置信 {analysis.confidence}</span>
                </div>
                <p>{analysis.summary}</p>
                <div className="radarBriefMeta">
                  {analysis.source ? <span>{sourceLabel(analysis.source)}</span> : null}
                  {analysis.generatedAt ? <span>{formatTime(analysis.generatedAt)}</span> : null}
                </div>
              </div>
              <div className="radarBriefGrid">
                <div className="radarBriefCard">
                  <span>市场要点</span>
                  <p>{compactHighlights.length ? compactHighlights.join("；") : "暂无要点，建议刷新 AI。"}</p>
                </div>
                <div className="radarBriefCard">
                  <span>风险</span>
                  <p>{compactRisks.length ? compactRisks.join("；") : "未返回额外风险，仍需控制仓位。"}</p>
                </div>
              </div>
              {displayWatchlist.length ? (
                <div className="radarBriefWatchlistFull" aria-label="重点观察 方向与入手价位">
                  <div className="radarWatchHead">
                    <span className="eyebrow">重点观察 · 方向与入手价位</span>
                    <span className="radarWatchHint">全市场候选池 · 研究参考</span>
                  </div>
                  <ul className="radarWatchlistItems">
                    {displayWatchlist.map((item) => {
                      const dir = radarDirectionView(item.direction);
                      return (
                        <li
                          key={item.instId}
                          className={item.isSelected ? "radarWatchSelected" : undefined}
                          aria-current={item.isSelected ? "true" : undefined}
                        >
                          <span className="radarWatchInst">{item.instId}</span>
                          {item.selectedNote ? <span className="radarWatchSelectedTag">{item.selectedNote}</span> : null}
                          <span className={`radarDirectionTag ${item.direction ? dir.tone : "neutral"}`}>
                            {item.direction ? dir.label : "方向待确认"}
                          </span>
                          <span className="radarWatchEntry">{item.entryZone || "参考盘面实时价位"}</span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : null}
              {sentimentView ? (
                <div className="radarBriefSentiment" aria-label="多空情绪">
                  <div className="radarSentimentHead">
                    <span className="eyebrow">多空情绪</span>
                    <span className={`radarSentimentTag ${sentimentView.tone}`}>{sentimentView.label}</span>
                  </div>
                  <div className="radarSentimentBar" role="img" aria-label={`样本 ${fundingSampled} 个，偏多 ${bullPct}%`}>
                    <span className="bull" style={{ width: `${bullPct}%` }} />
                    <span className="neu" style={{ width: `${neuPct}%` }} />
                    <span className="bear" style={{ width: `${bearPct}%` }} />
                  </div>
                  <div className="radarSentimentMetrics">
                    <div className="radarSentimentMetric">
                      <span>资金费率</span>
                      <p>{sentimentView.fundingText}</p>
                    </div>
                    <div className="radarSentimentMetric">
                      <span>持仓名义市值</span>
                      <p>{sentimentView.oiText}</p>
                    </div>
                  </div>
                </div>
              ) : null}
              <div className="radarBriefDisclaimer" aria-live="polite">
                <Info size={14} />
                <span>方向倾向与入手价位仅为研究参考，不构成投资建议；请独立决策并严格控制杠杆与止损。</span>
              </div>
              {compactAnalysisWarning ? (
                <div className="radarBriefWarning">
                  <ShieldAlert size={15} />
                  <span>{compactAnalysisWarning}</span>
                </div>
              ) : null}
              </>
            )
          ) : null}
        </Paper>
      ) : null}

      <section className="radarLayout">
        <Paper className="radarListPanel" p={0}>
          <PanelHeader
            icon={<BarChart3 size={17} />}
            title="候选排行"
            meta={`${visibleRadarResults.length}/${payload?.data.length ?? 0} 个 · ${activeSortLabel}${hasResultFilters ? " · 已筛选" : ""}`}
            action={payload ? (
              <Button
                className={`secondaryButton slim radarResultFilterToggle ${hasResultFilters ? "active" : ""}`}
                type="button"
                aria-expanded={resultFiltersExpanded}
                aria-controls="radar-result-filters"
                title="仅筛选本次扫描的候选结果"
                onClick={() => setResultFiltersExpanded((expanded) => !expanded)}
                variant="default"
                size="xs"
              >
                结果筛选
              </Button>
            ) : undefined}
          />
          {payload && resultFiltersExpanded ? (
            <div className="radarResultFilters" id="radar-result-filters" aria-label="本次扫描结果筛选">
              <span>本次结果</span>
              <Select className="radarResultFilter" label="波动" aria-label="本次扫描结果波动筛选" value={resultVolatility} onChange={(value) => setResultVolatility(value ?? "all")} data={[{ value: "all", label: "全部" }, { value: "high", label: "高波动" }, { value: "medium", label: "中波动" }, { value: "low", label: "低波动" }]} allowDeselect={false} size="xs" />
              <TextInput className="radarResultFilter" label="最小 24h 成交额" aria-label="本次扫描结果最小24小时成交额" value={resultMinTurnover} inputMode="decimal" placeholder="不限" onChange={(event) => setResultMinTurnover(event.target.value)} size="xs" />
              <Button className="secondaryButton slim radarClearResultFilters" type="button" onClick={clearResultFilters} disabled={!hasResultFilters} variant="default" size="xs">
                清除
              </Button>
            </div>
          ) : null}
          <div className="radarTableHeader">
            <span>合约</span>
            <span>机会</span>
            <span>方向</span>
            <span>{activeSortLabel}</span>
          </div>
          <div className="radarList" ref={radarListRef}>
            {loading && !payload ? (
              <div className="radarLoadingList">
                <DataLoadingSkeleton label="正在扫描合约候选" variant="radar-list" />
              </div>
            ) : visibleRadarResults.length ? (
              visibleRadarResults.map((item, index) => (
                <UnstyledButton
                  key={item.instId}
                  type="button"
                  className={`radarRow ${selectedResult?.instId === item.instId ? "selected" : ""}`}
                  onClick={() => setSelectedInstId(item.instId)}
                >
                  <span className="radarContract">
                    <strong>
                      #{index + 1} {item.instId}
                      {item.explainedBy === "llm" ? <span className="radarRowAi" title="方向与入手价位由 AI 解读生成">AI</span> : null}
                    </strong>
                    <small>{radarEntryLabel(item.entryAssessment)} · {radarTradabilityLabel(item.tradabilityStatus)} · {radarRiskLabel(item.riskLevel)}</small>
                  </span>
                  <span className={`radarScore ${radarScoreClass(item.scores.opportunity)}`}>
                    <strong>{item.scores.opportunity}</strong>
                    <span className="radarScoreHeat" aria-hidden="true">
                      <span style={{ width: `${Math.max(6, Math.min(100, Number(item.scores.opportunity ?? 0)))}%` }} />
                    </span>
                  </span>
                  {item.direction ? (
                    <span
                      className={`radarRowDir ${radarDirectionView(item.direction).tone}`}
                      title={item.entryZone ? `参考价位：${item.entryZone}` : "AI 研究方向倾向（仅供研究参考）"}
                    >
                      {radarDirectionView(item.direction).label}
                    </span>
                  ) : null}
                  <span title={radarTurnoverWindow(item, activeSort).warning || activeSortLabel}>{radarTurnoverCompact(item, activeSort)}</span>
                </UnstyledButton>
              ))
            ) : (
              <EmptyState className="radarListEmpty">
                <strong>{hasResultFilters ? "本次结果没有符合筛选的合约" : payload ? "没有符合条件的合约" : "设置条件后开始扫描"}</strong>
                <span>{hasResultFilters ? "已保留本次扫描快照；可清除结果筛选立即恢复候选。" : payload ? "可调整成交额、波动或风险提醒后重新扫描。" : "扫描会生成候选排行，并在右侧展示判断依据。"}</span>
                {hasResultFilters ? (
                  <Button className="secondaryButton slim radarClearResultFilters" type="button" onClick={clearResultFilters} variant="default" size="xs">
                    清除结果筛选
                  </Button>
                ) : null}
              </EmptyState>
            )}
          </div>
        </Paper>

        <Paper className="radarDetailPanel">
          {loading && !selectedResult ? (
            <div className="radarLoadingDetail">
              <DataLoadingSkeleton label="正在读取候选合约详情" variant="radar-detail" />
            </div>
          ) : selectedResult ? (
            <>
              <div className="radarDetailHeader">
                <div>
                  <span className="eyebrow">当前关注</span>
                  <h2>{selectedResult.instId}</h2>
                  <p>{selectedResult.instFamily || "SWAP"} · {radarEntryLabel(selectedResult.entryAssessment)} · {radarTradabilityLabel(selectedResult.tradabilityStatus)} · {stateLabel(selectedResult.state)}</p>
                </div>
                <div className={`radarBigScore ${radarScoreClass(selectedResult.scores.opportunity)}`}>
                  <span>机会分</span>
                  <strong>{selectedResult.scores.opportunity}</strong>
                </div>
              </div>

              <div className="radarScoreGrid">
                <Metric label={activeSortLabel} value={radarTurnoverCompact(selectedResult, activeSort)} />
                <Metric label={radarLiquidityBasisLabel(selectedResult.liquidity)} value={radarLiquidityCompact(selectedResult)} />
                <Metric label="24h 振幅" value={`${formatValue(selectedResult.range24hPct)}%`} />
                <Metric label="风险提醒" value={radarRiskSummary(selectedResult.riskLevel)} />
              </div>

              {selectedResult.direction || selectedResult.entryZone ? (
                <div className={`radarTradeRef ${selectedResult.direction ? radarDirectionView(selectedResult.direction).tone : "neutral"}`}>
                  <div className="radarTradeRefHead">
                    <span className="eyebrow">交易参考 · 研究</span>
                    <span className={`radarDirectionTag ${selectedResult.direction ? radarDirectionView(selectedResult.direction).tone : "neutral"}`}>
                      {selectedResult.direction ? radarDirectionView(selectedResult.direction).label : "方向待确认"}
                    </span>
                  </div>
                  <div className="radarTradeRefBody">
                    <div>
                      <span>方向倾向</span>
                      <strong>{selectedResult.direction ? radarDirectionView(selectedResult.direction).label : "待确认"}</strong>
                    </div>
                    <div>
                      <span>参考入手价位</span>
                      <strong>{selectedResult.entryZone || "参考盘面实时价位"}</strong>
                    </div>
                  </div>
                  <p className="radarTradeRefSource">
                    {selectedResult.explainedBy === "llm" ? "由 AI 解读生成" : "由指标规则生成"} · 仅供研究参考，非投资建议
                  </p>
                </div>
              ) : null}

              <RadarFlowSnapshot stats={radarFlowStats} />

              {payload?.sort?.candidateScope ? <p className="radarScopeNote">{payload.sort.candidateScope}</p> : null}

              <div className={`radarEntryPanel ${radarEntryClass(selectedResult.entryAssessment)}`}>
                <div>
                  <span>入手判断</span>
                  <strong>{radarEntryLabel(selectedResult.entryAssessment)}</strong>
                </div>
                <p>{selectedResult.entryAssessment?.summary || "等待成交量与浮动数据确认。"}</p>
                <small>
                  {(selectedResult.entryAssessment?.drivers?.length ? selectedResult.entryAssessment.drivers : [
                    `${radarLiquidityBasisLabel(selectedResult.liquidity)} ${radarLiquidityCompact(selectedResult)}`,
                    `24h 振幅 ${formatValue(selectedResult.range24hPct)}%`
                  ]).slice(0, 4).join(" · ")}
                </small>
                <p className="radarMarketConditionNote">
                  <strong>行情状态：{radarMarketCondition(selectedResult.marketCondition).label}</strong>
                  {" · "}{radarMarketCondition(selectedResult.marketCondition).summary}
                </p>
              </div>

              <div className="radarTags">
                {Array.from(new Set([
                  radarMarketCondition(selectedResult.marketCondition).label || "方向待确认",
                  radarVolatilityLabel(selectedResult.volatilityLevel),
                  radarRiskLabel(selectedResult.riskLevel),
                  ...selectedResult.tags
                ])).map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>

              <Disclosure className="radarEvidenceDetails" label="查看关注理由与风险提示">
                <div className="radarReasonGrid">
                  <div>
                    <h3>关注理由</h3>
                    {selectedResult.reasons.length ? (
                      selectedResult.reasons.slice(0, 2).map((item, index) => <p key={`${item}-${index}`}>{item}</p>)
                    ) : (
                      <p>当前只有指标评分，建议结合行情图进一步确认。</p>
                    )}
                  </div>
                  <div>
                    <h3>风险提示</h3>
                    {selectedResult.warnings.length ? (
                      selectedResult.warnings.slice(0, 2).map((item, index) => <p key={`${item}-${index}`}>{item}</p>)
                    ) : (
                      <p>未发现明显数据风险，仍需控制仓位和止损。</p>
                    )}
                  </div>
                </div>
              </Disclosure>

              <div className="radarActionBar">
                <Button type="button" className="secondaryButton" onClick={() => onOpenContract(selectedResult.instId, "market")} variant="default" size="xs" leftSection={<ChartCandlestick size={16} />}>
                  看行情
                </Button>
                <Button type="button" className="secondaryButton" onClick={() => onOpenContract(selectedResult.instId, "aiOutlook")} variant="default" size="xs" leftSection={<BrainCircuit size={16} />}>
                  AI解读
                </Button>
                <Button type="button" className="secondaryButton" onClick={() => onOpenContract(selectedResult.instId, "stats")} variant="default" size="xs" leftSection={<Database size={16} />}>
                  交易数据
                </Button>
                <Button type="button" className="secondaryButton" onClick={() => onOpenContract(selectedResult.instId, "trade")} variant="default" size="xs" leftSection={<Send size={16} />}>
                  手动交易
                </Button>
                <Button type="button" className="primaryButton" onClick={() => onOpenContract(selectedResult.instId, "automation")} size="xs" leftSection={<Bot size={16} />}>
                  配置策略
                </Button>
              </div>
            </>
          ) : (
            <EmptyState className="radarDetailEmpty">
              <Search size={18} aria-hidden="true" />
              <strong>{hasResultFilters ? "调整结果筛选后查看合约详情" : payload ? "请选择一个合约查看详情" : "扫描完成后查看合约详情"}</strong>
              <span>{hasResultFilters ? "当前快照没有符合波动或成交额条件的合约。" : payload ? "从左侧候选排行选择合约。" : "候选会按已选成交额口径排序，并保留风险提醒与行情状态说明。"}</span>
              {hasResultFilters ? (
                <Button variant="default" size="xs" className="secondaryButton slim radarClearResultFilters" type="button" onClick={clearResultFilters}>
                  清除结果筛选
                </Button>
              ) : null}
            </EmptyState>
          )}
        </Paper>
      </section>
    </section>
  );
}

function useMarketInstrumentRows({
  instruments,
  filter,
  query,
  selected,
  sortMode,
  tickers,
  limit = 2000
}: {
  instruments: Instrument[];
  filter: InstrumentFilter;
  query: string;
  selected: string;
  sortMode: InstrumentSort;
  tickers: Record<string, Ticker>;
  limit?: number;
}) {
  const filteredInstruments = React.useMemo(() => {
    return instruments.filter((item) => {
      if (filter === "watch") return Boolean(item.watched);
      if (filter === "usdt") return isUsdtSettled(item);
      if (filter === "coin") return isCoinSettled(item);
      if (filter === "live") return item.state === "live";
      return true;
    });
  }, [filter, instruments]);

  const displayedInstruments = React.useMemo(() => {
    const keyword = query.trim().toUpperCase();
    const filtered = filteredInstruments.filter((item) => instrumentMatchesKeyword(item, keyword));
    return [...filtered]
      .sort((left, right) => compareInstrumentRelevance(left, right, { selectedInstId: selected, sortMode, tickers }))
      .slice(0, limit);
  }, [filteredInstruments, limit, query, selected, sortMode, tickers]);

  const realtimeSubscriptionInstruments = React.useMemo(() => {
    const keyword = query.trim().toUpperCase();
    return [...filteredInstruments.filter((item) => instrumentMatchesKeyword(item, keyword))]
      .sort((left, right) =>
        compareInstrumentRelevance(left, right, { selectedInstId: selected, sortMode: "default", tickers: {} })
      )
      .slice(0, 80);
  }, [filteredInstruments, query, selected]);

  return { filteredInstruments, displayedInstruments, realtimeSubscriptionInstruments };
}

function MarketInstrumentRail({
  icon,
  title,
  selected,
  query,
  onQueryChange,
  filter,
  onFilterChange,
  sortMode,
  onSortModeChange,
  watchedCount,
  totalCount,
  displayedInstruments,
  loading,
  emptyState,
  tickers,
  collapsed,
  onToggleCollapsed,
  onRefresh,
  onSelectContract,
  onToggleWatch
}: {
  icon: React.ReactNode;
  title: string;
  selected: string;
  query: string;
  onQueryChange: (value: string) => void;
  filter: InstrumentFilter;
  onFilterChange: (value: InstrumentFilter) => void;
  sortMode: InstrumentSort;
  onSortModeChange: (value: InstrumentSort) => void;
  watchedCount: number;
  totalCount: number;
  displayedInstruments: Instrument[];
  loading: boolean;
  emptyState?: React.ReactNode;
  tickers: Record<string, Ticker>;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onRefresh: () => void;
  onSelectContract: (instId: string) => void;
  onToggleWatch: (instrument: Instrument) => void;
}) {
  const activeAdvancedFilter = advancedInstrumentFilters.find((item) => item.key === filter);
  const activeSort = instrumentSorts.find((item) => item.key === sortMode) ?? instrumentSorts[0];

  const selectFilter = (value: InstrumentFilter) => {
    onFilterChange(value);
  };

  const selectSort = (value: InstrumentSort) => {
    onSortModeChange(value);
  };

  return (
    <aside className={`marketRail ${collapsed ? "collapsed" : ""}`}>
      <div className="marketRailCollapsedHeader">
        <IconButton label="展开合约列表" onClick={onToggleCollapsed}>
          <ChevronRight size={17} />
        </IconButton>
      </div>
      <div className="marketRailExpandedContent">
        <PanelHeader
          icon={icon}
          title={title}
          meta={`已关注 ${watchedCount} · 全部 ${totalCount}`}
          action={
            <div className="marketRailHeaderActions">
              <span className="collapseRailAction">
                <IconButton label="收起合约列表" onClick={onToggleCollapsed}>
                  <ChevronLeft size={17} />
                </IconButton>
              </span>
              <ActionIcon type="button" className="iconButton" aria-label="刷新合约列表" title="刷新合约列表" onClick={onRefresh} disabled={loading} aria-busy={loading} variant="subtle" color="workspace">
                <RefreshCw size={16} />
              </ActionIcon>
            </div>
          }
        />
      <TextInput
        className="searchBox"
        value={query}
        onChange={(event) => onQueryChange(event.target.value.toUpperCase())}
        placeholder="搜索 BTC / ETH / USDT"
        aria-label="搜索合约"
        leftSection={<Search size={16} aria-hidden="true" />}
      />
      <div className="instrumentQuickControls" aria-label="合约范围与排序">
        <SegmentedControl
          className="primaryInstrumentFilters"
          aria-label="常用合约范围"
          value={filter}
          onChange={(value) => selectFilter(value as InstrumentFilter)}
          data={primaryInstrumentFilters.map((item) => ({ value: item.key, label: item.label }))}
          fullWidth
          size="xs"
        />
        <Group className="instrumentControlMenus" gap="xs" grow>
          <Menu withinPortal position="bottom-start">
            <Menu.Target>
              <Button className={activeAdvancedFilter ? "selected" : ""} variant="default" rightSection={<ChevronDown size={14} />} size="xs">
                {activeAdvancedFilter ? `筛选：${activeAdvancedFilter.label}` : "筛选"}
              </Button>
            </Menu.Target>
            <Menu.Dropdown aria-label="更多合约范围">
              {advancedInstrumentFilters.map((item) => (
                <Menu.Item key={item.key} onClick={() => selectFilter(item.key)} rightSection={filter === item.key ? <Check size={14} /> : null}>
                  {item.label}
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
          <Menu withinPortal position="bottom-end">
            <Menu.Target>
              <Button variant="default" rightSection={<ChevronDown size={14} />} size="xs">{`排序：${activeSort.label}`}</Button>
            </Menu.Target>
            <Menu.Dropdown aria-label="合约排序方式">
              {instrumentSorts.map((item) => (
                <Menu.Item key={item.key} onClick={() => selectSort(item.key)} rightSection={sortMode === item.key ? <Check size={14} /> : null}>
                  {item.label}
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
        </Group>
      </div>

      <ScrollArea className="instrumentList" type="auto" scrollbarSize={8}>
        {loading && displayedInstruments.length === 0 ? (
          <DataLoadingSkeleton variant="rail" label="正在读取合约列表" />
        ) : displayedInstruments.length === 0 ? (
          emptyState ?? <EmptyState compact>没有符合条件的合约</EmptyState>
        ) : (
          displayedInstruments.map((item) => {
            const itemTicker = tickers[item.inst_id];
            const itemChange = tickerTodayChange(itemTicker);
            const itemAssetName = instrumentAssetName(item, item.inst_id);
            return (
              <div key={item.inst_id} className={`instrument ${selected === item.inst_id ? "active" : ""}`}>
                <UnstyledButton
                  type="button"
                  className="instrumentMain"
                  onClick={() => onSelectContract(item.inst_id)}
                  aria-current={selected === item.inst_id ? "true" : undefined}
                  title={`${instrumentSummaryLabel(item, item.inst_id)} · ${stateLabel(item.state)} · ${instrumentActivityLabel(itemTicker, item.inst_id)} · 今日涨跌 ${formatSignedPercent(itemChange.percent)}`}
                >
                  <span className="instrumentAvatar">
                    {instrumentAvatarText(item.inst_id)}
                  </span>
                  <div className="instrumentIdentity">
                    <span className="instrumentNameLine">
                      <strong>{instrumentDisplaySymbol(item.inst_id)}</strong>
                      <Badge className="instrumentTypeTag">{instrumentContractTypeLabel(item, item.inst_id)}</Badge>
                    </span>
                    <span
                      className="instrumentSubtitle"
                      title={`${itemAssetName} · ${instrumentSettlementLabel(item, item.inst_id)} · ${instrumentActivityLabel(itemTicker, item.inst_id)} · ${instrumentSummaryLabel(item, item.inst_id)}`}
                    >
                      {itemAssetName} · {instrumentSettlementLabel(item, item.inst_id)} · {instrumentActivityLabel(itemTicker, item.inst_id)}
                    </span>
                  </div>
                  <div className="instrumentQuote">
                    <span className="instrumentPrice">{formatMarketNumber(itemTicker?.last)}</span>
                    <span
                      className={`instrumentChange ${changeClass(itemChange.percent)}`}
                      title="今日涨跌（按 UTC+8 日开盘价计算）"
                      aria-label={`今日涨跌 ${formatSignedPercent(itemChange.percent)}`}
                    >
                      {formatSignedPercent(itemChange.percent)}
                    </span>
                  </div>
                </UnstyledButton>
                <ActionIcon
                  type="button"
                  className="watchButton"
                  onClick={(event) => {
                    event.stopPropagation();
                    onToggleWatch(item);
                  }}
                  aria-label={item.watched ? "取消关注" : "关注合约"}
                  variant="subtle"
                  color="yellow"
                >
                  <Star size={16} weight={item.watched ? "fill" : "regular"} />
                </ActionIcon>
              </div>
            );
          })
        )}
      </ScrollArea>
      {loading && displayedInstruments.length > 0 ? <DataLoadingState label="合约列表更新中" compact /> : null}
      </div>
    </aside>
  );
}

function MarketContractWorkspace({
  selected,
  activeBar,
  initialFilter,
  onSelectContract,
  onSelectBar,
  children
}: {
  selected: string;
  activeBar: string;
  initialFilter: InstrumentFilter;
  onSelectContract: (instId: string) => void;
  onSelectBar: (bar: string) => void;
  children: React.ReactNode;
}) {
  const [query, setQuery] = React.useState("");
  const [filter, setFilter] = React.useState<InstrumentFilter>(initialFilter);
  const [sortMode, setSortMode] = React.useState<InstrumentSort>("default");
  const [railCollapsed, setRailCollapsed] = React.useState(false);
  const [instruments, setInstruments] = React.useState<Instrument[]>([]);
  const [instrumentsLoading, setInstrumentsLoading] = React.useState(false);
  const [tickers, setTickers] = React.useState<Record<string, Ticker>>({});
  const [tickersLoading, setTickersLoading] = React.useState(false);
  const [tickerUpdatedAt, setTickerUpdatedAt] = React.useState<number | null>(null);
  const [tickerSource, setTickerSource] = React.useState("等待数据");
  const [tickerRefresh, setTickerRefresh] = React.useState<TickerRefresh | null>(null);
  const [warning, setWarning] = React.useState("");
  const chartBar = normalizeRouteBar(activeBar);
  const [chartCandles, setChartCandles] = React.useState<Candle[]>([]);
  const [chartLoading, setChartLoading] = React.useState(false);
  const [chartSnapshot, setChartSnapshot] = React.useState<ChartSnapshotMetadata | null>(null);
  const [chartSource, setChartSource] = React.useState("等待数据");
  const [chartUpdatedAt, setChartUpdatedAt] = React.useState<number | null>(null);
  const [chartLastPushedAt, setChartLastPushedAt] = React.useState<number | null>(null);
  const [chartWarning, setChartWarning] = React.useState("");

  const loadInstruments = React.useCallback(async () => {
    setInstrumentsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/instruments?limit=2000`);
      if (!response.ok) throw new Error("合约列表加载失败");
      const payload = await response.json();
      setInstruments(payload.data ?? []);
    } finally {
      setInstrumentsLoading(false);
    }
  }, []);

  const loadTickers = React.useCallback(async () => {
    setTickersLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/tickers`);
      if (!response.ok) throw new Error("Ticker 快照加载失败");
      const payload = (await response.json()) as TickersResponse;
      const rows: Ticker[] = payload.data ?? [];
      setTickers(
        rows.reduce<Record<string, Ticker>>((next, item) => {
          if (item.instId) next[item.instId] = item;
          return next;
        }, {})
      );
      setTickerUpdatedAt(payload.ts ?? Date.now());
      setTickerSource(payload.source ?? (rows.length ? "okx-rest" : "等待数据"));
      setTickerRefresh(payload.refresh ?? null);
      setWarning(payload.warning ?? "");
    } finally {
      setTickersLoading(false);
    }
  }, []);

  const refreshInstruments = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/instruments/refresh`, { method: "POST" });
    if (!response.ok) throw new Error("合约列表刷新失败");
    await loadInstruments();
  }, [loadInstruments]);

  React.useEffect(() => {
    loadInstruments().catch(() => setWarning("合约列表加载失败"));
  }, [loadInstruments]);

  React.useEffect(() => {
    loadTickers().catch(() => undefined);
    const refreshVisibleTickers = () => {
      if (!document.hidden) loadTickers().catch(() => undefined);
    };
    const timer = window.setInterval(refreshVisibleTickers, TICKER_POLL_MS);
    document.addEventListener("visibilitychange", refreshVisibleTickers);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshVisibleTickers);
    };
  }, [loadTickers]);

  const { filteredInstruments, displayedInstruments, realtimeSubscriptionInstruments } = useMarketInstrumentRows({
    instruments,
    filter,
    query,
    selected,
    sortMode,
    tickers
  });
  const railRealtimeInstIds = React.useMemo(
    () => Array.from(new Set([selected, ...realtimeSubscriptionInstruments.map((item) => item.inst_id)])),
    [realtimeSubscriptionInstruments, selected]
  );

  const tickerRealtime = useRealtimeFeed({
    topics: ["market.ticker"],
    instId: selected,
    instIds: railRealtimeInstIds,
    onSnapshotRequired: () => {
      loadTickers().catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "market.ticker") {
        const tickerPayload = (payload.data as Ticker) ?? null;
        if (!payload.instId || !tickerPayload) return;
        setTickers((current) => ({ ...current, [payload.instId as string]: tickerPayload }));
        setTickerUpdatedAt(payload.ts ?? Date.now());
        setTickerSource(payload.source ?? "okx-ws");
      }
      if (payload.type === "status") {
        if (payload.source === "partial-fallback" && payload.skippedInstIds?.includes(selected)) {
          setTickerSource("rest-fallback");
        } else {
          setTickerSource(payload.source ?? "okx-ws");
        }
      }
      if (payload.type === "error" || payload.type === "disabled") {
        setTickerSource("rest-fallback");
      }
    }
  });

  const loadChartSnapshot = React.useCallback(async (force = false): Promise<ChartSnapshotMetadata | null> => {
    setChartLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/candles?instId=${encodeURIComponent(selected)}&bar=${encodeURIComponent(chartBar)}&limit=200${force ? "&force=true" : ""}`);
      if (!response.ok) throw new Error("K线快照加载失败");
      const payload = await response.json();
      const rows = normalizeCandleBatch((payload.data as Candle[]) ?? []);
      const snapshot = (payload.snapshot as ChartSnapshotMetadata | undefined) ?? null;
      setChartCandles(rows);
      setChartSnapshot(snapshot);
      setChartSource(payload.source ?? "okx-rest");
      setChartUpdatedAt(payload.ts ?? Date.now());
      setChartLastPushedAt(payload.ts ?? Date.now());
      setChartWarning(payload.warning ? compactRealtimeWarning(payload.warning) : "");
      return snapshot;
    } finally {
      setChartLoading(false);
    }
  }, [chartBar, selected]);

  React.useEffect(() => {
    setChartCandles([]);
    setChartSnapshot(null);
    setChartSource("连接中");
    setChartUpdatedAt(null);
    setChartLastPushedAt(null);
    setChartWarning("");
  }, [chartBar, selected]);

  React.useEffect(() => {
    loadChartSnapshot().catch((error) => setChartWarning(error instanceof Error ? error.message : "K线快照加载失败"));
  }, [loadChartSnapshot]);

  const chartRealtime = useRealtimeFeed({
    topics: ["market.candles"],
    instId: selected,
    bar: chartBar,
    onSnapshotRequired: () => {
      loadChartSnapshot().catch((error) => setChartWarning(error instanceof Error ? error.message : "K线快照加载失败"));
    },
    onEvent: (payload) => {
      if (payload.type === "market.candles" && payload.instId === selected && payload.bar === chartBar) {
        const nextSource = payload.source ?? "unknown";
        setChartCandles(normalizeCandleBatch((payload.data as Candle[]) ?? []));
        setChartSnapshot((payload.snapshot as ChartSnapshotMetadata | undefined) ?? null);
        setChartSource(nextSource);
        setChartUpdatedAt(payload.ts ?? Date.now());
        setChartLastPushedAt(payload.ts ?? Date.now());
        setChartWarning(
          payload.warning
            ? compactRealtimeWarning(payload.warning)
            : isDegradedCandleSource(nextSource)
              ? "K线历史暂不完整，正在等待 OKX 快照。"
              : ""
        );
      }
      if (payload.type === "status" && payload.topic === "market.candles") {
        setChartLastPushedAt(payload.ts ?? Date.now());
      }
      if (payload.type === "error" || payload.type === "disabled") {
        if (payload.topic === "market.candles") {
          setChartSource("rest-fallback");
          setChartWarning(compactRealtimeWarning(payload.message ?? payload.warning, payload.topic));
        }
      }
    }
  });

  const toggleWatch = async (instrument: Instrument) => {
    const watched = Boolean(instrument.watched);
    const response = await fetch(`${API_BASE}/api/watchlist/${instrument.inst_id}`, { method: watched ? "DELETE" : "PUT" });
    if (!response.ok) throw new Error("关注列表更新失败");
    await loadInstruments();
  };

  const showWatchlistEmptyState =
    filter === "watch" && query.trim() === "" && instruments.length > 0 && filteredInstruments.length === 0;
  const snapshot = React.useMemo<MarketContractWorkspaceSnapshot>(
    () => ({
      selected, instruments, instrumentsLoading, tickers, tickersLoading, tickerUpdatedAt, tickerSource, tickerRefresh, warning, tickerRealtime,
      chartBar, setChartBar: onSelectBar, chartCandles, chartLoading, chartSnapshot, chartSource,
      chartUpdatedAt, chartLastPushedAt, chartWarning, chartRealtime, refreshChartSnapshot: loadChartSnapshot
    }),
    [chartBar, chartCandles, chartLastPushedAt, chartLoading, chartRealtime, chartSnapshot, chartSource, chartUpdatedAt, chartWarning, instruments, instrumentsLoading, loadChartSnapshot, onSelectBar, selected, tickerRealtime, tickerRefresh, tickerSource, tickerUpdatedAt, tickers, tickersLoading, warning]
  );

  return (
    <section className={`marketLayout marketContractWorkspace ${railCollapsed ? "marketRailCollapsed" : ""}`}>
      <MarketContractWorkspaceContext.Provider value={snapshot}>
        <MarketInstrumentRail
        icon={<BarChart3 size={17} />}
        title="合约"
        selected={selected}
        query={query}
        onQueryChange={setQuery}
        filter={filter}
        onFilterChange={setFilter}
        sortMode={sortMode}
        onSortModeChange={setSortMode}
        watchedCount={instruments.filter((item) => Boolean(item.watched)).length}
        totalCount={instruments.length}
        displayedInstruments={displayedInstruments}
        loading={instrumentsLoading}
        collapsed={railCollapsed}
        onToggleCollapsed={() => setRailCollapsed((current) => !current)}
        emptyState={
          showWatchlistEmptyState ? (
            <EmptyState compact className="watchlistEmptyState">
              <span>暂无本地已关注合约</span>
              <Button type="button" variant="default" size="xs" className="secondaryButton slim" onClick={() => setFilter("all")}>
                查看全部合约
              </Button>
            </EmptyState>
          ) : warning ? (
            <EmptyState compact>{warning}</EmptyState>
          ) : undefined
        }
        tickers={tickers}
        onRefresh={() => refreshInstruments().catch((error) => setWarning(error.message))}
        onSelectContract={onSelectContract}
        onToggleWatch={(instrument) => toggleWatch(instrument).catch((error) => setWarning(error.message))}
        />
        {children}
      </MarketContractWorkspaceContext.Provider>
    </section>
  );
}

type OrderBookLevel = { price: string; size: string; cumulative: string };
type OrderBookSnapshot = {
  instId: string;
  asks: OrderBookLevel[];
  bids: OrderBookLevel[];
  spread: { absolute: string; percent: string } | null;
  ts: number;
  receivedAt: number;
  warning: string;
};
type OrderBookResponse = {
  instId: string;
  data: OrderBookSnapshot | null;
  state: "fresh" | "loading" | "updating" | "cached" | "empty" | "unavailable";
  message: string;
  cacheAgeMs: number | null;
  ts: number | null;
};

function MarketOrderBook({ instId }: { instId: string }) {
  const [response, setResponse] = React.useState<OrderBookResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [depth, setDepth] = React.useState("5");

  React.useEffect(() => {
    let active = true;
    let inFlight = false;
    let controller: AbortController | null = null;
    setResponse(null);
    setLoading(true);

    const load = async () => {
      if (!active || document.hidden || inFlight) return;
      inFlight = true;
      controller = new AbortController();
      try {
        const result = await fetch(`${API_BASE}/api/market/order-book?instId=${encodeURIComponent(instId)}`, { signal: controller.signal });
        if (!result.ok) throw new Error("盘口暂不可用");
        const next = (await result.json()) as OrderBookResponse;
        if (active && next.instId === instId) setResponse(next);
      } catch {
        if (active) setResponse((current) => ({
          instId,
          data: current?.instId === instId && current.data && Date.now() - current.data.ts <= 15_000 ? current.data : null,
          state: "unavailable",
          message: "盘口更新失败，请稍后重试。",
          cacheAgeMs: null,
          ts: null
        }));
      } finally {
        inFlight = false;
        if (active) setLoading(false);
      }
    };

    const onVisibilityChange = () => {
      if (!document.hidden) load().catch(() => undefined);
    };
    load().catch(() => undefined);
    const timer = window.setInterval(() => load().catch(() => undefined), 3_000);
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      active = false;
      controller?.abort();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [instId]);

  const current = response?.instId === instId ? response : null;
  const snapshot = current?.data && Date.now() - current.data.ts <= 15_000 ? current.data : null;
  const expired = current?.data && !snapshot;
  const state = loading && !current ? "loading" : expired ? "unavailable" : snapshot && current?.state === "unavailable" ? "cached" : current?.state ?? "unavailable";
  const message = expired ? "盘口快照已过期，请等待更新。" : state === "cached" && current?.state === "unavailable" ? "盘口更新失败，当前显示最近缓存。" : current?.message ?? "正在读取当前合约盘口。";
  const askRows = snapshot?.asks.slice(0, Number(depth)).reverse() ?? [];
  const bidRows = snapshot?.bids.slice(0, Number(depth)) ?? [];
  const hasRows = askRows.length > 0 || bidRows.length > 0;
  const showStatusDetail = state !== "fresh";

  return <section className="marketOrderBook" aria-label={`${instId} 只读盘口`} aria-busy={state === "loading" || state === "updating"}>
    <div className="marketOrderBookHeader">
      <div className="marketOrderBookTitle">
        <strong title={`${instId} · 买卖盘口`}>盘口</strong>
        <span>{snapshot ? `报价 ${new Date(snapshot.ts).toLocaleTimeString("zh-CN")}` : "公开行情"}</span>
      </div>
      <SegmentedControl
        className="marketOrderBookDepth"
        aria-label="盘口档位"
        value={depth}
        onChange={setDepth}
        data={[{ value: "5", label: "5档" }, { value: "10", label: "10档" }]}
        disabled={!hasRows}
        size="xs"
      />
      <Badge color={state === "fresh" ? "teal" : state === "loading" || state === "empty" ? "gray" : "yellow"} variant="light">
        {state === "fresh" ? "已更新" : state === "loading" ? "加载中" : state === "updating" ? "更新中" : state === "cached" ? "缓存" : state === "empty" ? "暂无档位" : "不可用"}
      </Badge>
    </div>
    {showStatusDetail ? <p className="marketOrderBookStatus" role="status" aria-live="polite">
      {message}{snapshot && (state === "cached" || state === "updating") ? ` · ${Math.floor(Math.max(0, Date.now() - snapshot.ts) / 1000)} 秒前` : ""}
    </p> : null}
    {snapshot?.warning ? <p className="marketOrderBookWarning">{snapshot.warning}</p> : null}
    {hasRows ? <div className="marketOrderBookTableWrap" tabIndex={0} aria-label={`${instId} 买卖盘口档位`}><table className="marketOrderBookTable">
      <thead><tr><th scope="col">价格</th><th scope="col">数量（张）</th><th scope="col">累计（张）</th></tr></thead>
      <tbody>
        <tr className="marketOrderBookSide"><th scope="rowgroup" colSpan={3}>卖盘</th></tr>
        {askRows.map((level) => <tr className="ask" key={`ask-${level.price}`}><td>{level.price}</td><td>{level.size}</td><td>{level.cumulative}</td></tr>)}
        <tr className="marketOrderBookSpread"><td colSpan={3}>{snapshot?.spread ? `买卖价差 ${snapshot.spread.absolute} · ${snapshot.spread.percent}%` : "买卖价差暂不可用"}</td></tr>
        <tr className="marketOrderBookSide"><th scope="rowgroup" colSpan={3}>买盘</th></tr>
        {bidRows.map((level) => <tr className="bid" key={`bid-${level.price}`}><td>{level.price}</td><td>{level.size}</td><td>{level.cumulative}</td></tr>)}
      </tbody>
    </table></div> : <div className="marketOrderBookEmpty">{state === "loading" ? "正在读取盘口档位" : state === "empty" ? "当前合约暂无盘口档位" : "盘口暂不可用，图表仍可继续查看"}</div>}
  </section>;
}

function MarketPage({
  onOpenAiOutlook
}: {
  onOpenAiOutlook?: (instId: string, bar: string) => void;
}) {
  const {
    selected, instruments, instrumentsLoading, tickers, tickersLoading, tickerUpdatedAt, tickerSource, tickerRefresh, tickerRealtime, warning: workspaceWarning,
    chartBar: bar, setChartBar: setBar, chartCandles: candles, chartSource: candleSource,
    chartLoading, chartUpdatedAt: candleUpdatedAt, chartLastPushedAt: lastPushedAt, chartWarning: candleWarning,
    chartRealtime: marketRealtime
  } = useMarketContractWorkspace();
  const [hoveredCandleTime, setHoveredCandleTime] = React.useState<number | null>(null);
  const [candleDetail, setCandleDetail] = React.useState<CandleDetailSnapshot | null>(null);
  const [visibleLogicalRange, setVisibleLogicalRange] = React.useState<LogicalRange | null>(null);
  const [chartClock, setChartClock] = React.useState(() => Date.now());
  const chartContainer = React.useRef<HTMLDivElement | null>(null);
  const chartRef = React.useRef<IChartApi | null>(null);
  const seriesRef = React.useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = React.useRef<ISeriesApi<"Histogram"> | null>(null);
  const movingAverageSeriesRef = React.useRef<Record<MovingAverageKey, ISeriesApi<"Line">> | null>(null);
  const extremaMarkersRef = React.useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const hasFittedChartRef = React.useRef(false);
  const previousCandleCountRef = React.useRef(0);
  const openCandleAtTimeRef = React.useRef<(time: number) => void>(() => undefined);

  const selectedInstrument = React.useMemo(
    () => instruments.find((item) => item.inst_id === selected),
    [instruments, selected]
  );

  const latestCandle = candles[candles.length - 1];
  const selectedTicker = tickers[selected] ?? null;
  const livePrice = selectedTicker?.last ?? latestCandle?.close;
  const dayChange = tickerChangeFromBases(selectedTicker, ["sodUtc8"]);
  const dayChangeClass = changeClass(dayChange.percent);
  const activity24h = market24hActivity(selectedTicker, selected);
  const hasVolume = candles.some((item) => item.volume !== undefined && item.volume !== "" && Number.isFinite(Number(item.volume)) && Number(item.volume) >= 0);
  const tickerFreshness = tickerRefreshStatus(tickerRefresh, tickerRealtime.connected);
  const visibleWarning = candleWarning
    ? compactRealtimeWarning(candleWarning, "market.candles")
    : tickerRealtime.warning
      ? compactRealtimeWarning(tickerRealtime.warning, "market.ticker")
      : compactRealtimeWarning(workspaceWarning, "market.ticker");
  const candleByChartTime = React.useMemo(() => {
    const next = new Map<number, Candle>();
    candles.forEach((item) => {
      const key = candleChartTime(item);
      if (key !== null) next.set(key, item);
    });
    return next;
  }, [candles]);
  const detailCandle = hoveredCandleTime === null ? latestCandle : candleByChartTime.get(hoveredCandleTime) ?? latestCandle;
  const detailCandleIndex = React.useMemo(() => {
    if (!detailCandle) return -1;
    return candles.findIndex((item) => String(item.ts) === String(detailCandle.ts));
  }, [candles, detailCandle]);
  const previousDetailCandle = detailCandleIndex > 0 ? candles[detailCandleIndex - 1] : null;
  const detailCandleDelta = candleDelta(detailCandle, previousDetailCandle);
  const detailCandlePercent = displayCandlePercent(detailCandleDelta.percent);
  const detailCandleDeltaClass = detailCandlePercent === 0 ? "" : changeClass(detailCandlePercent);
  const movingAverages = React.useMemo(() => calculateMovingAverages(candles), [candles]);
  const detailCandleTime = candleChartTime(detailCandle);
  const trendLegendValues = detailCandleTime === null ? undefined : movingAverages.valuesByTime.get(detailCandleTime);
  const openCandleDetail = (candle: Candle | null | undefined) => {
    if (!candle) return;
    const index = candles.findIndex((item) => String(item.ts) === String(candle.ts));
    const previous = index > 0 ? candles[index - 1] : null;
    const chartTime = candleChartTime(candle);
    const averages = chartTime === null ? null : movingAverages.valuesByTime.get(chartTime) ?? null;
    setCandleDetail({
      instId: selected,
      bar,
      candle: { ...candle },
      previous: previous ? { ...previous } : null,
      averages: averages ? { ...averages } : null,
      source: candleSource
    });
  };
  openCandleAtTimeRef.current = (time) => openCandleDetail(candleByChartTime.get(time));
  const selectedCandleDelta = candleDelta(candleDetail?.candle, candleDetail?.previous);
  const selectedCandlePercent = displayCandlePercent(selectedCandleDelta.percent);
  const selectedCandleAmplitude = candleAmplitude(candleDetail?.candle);
  const visibleExtrema = React.useMemo(
    () => visibleCandleExtrema(candles, visibleLogicalRange),
    [candles, visibleLogicalRange]
  );
  const activeCandleCountdown = candleCloseCountdown(latestCandle, bar, chartClock);
  const formattedCandleCountdown = formatCloseCountdown(activeCandleCountdown);
  const candleSourceLive = isLiveCandleSource(candleSource);
  const candleStreamLive = marketRealtime.connected && candleSourceLive;
  const initialTickerLoading = tickersLoading && Object.keys(tickers).length === 0;
  const initialChartLoading = chartLoading && candles.length === 0;

  React.useEffect(() => {
    if (!chartContainer.current) return;
    const chart = createChart(chartContainer.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#465261",
        attributionLogo: false
      },
      grid: {
        vertLines: { color: "#e7edf4" },
        horzLines: { color: "#e7edf4" }
      },
      rightPriceScale: { borderColor: "#d9e2ec" },
      timeScale: { borderColor: "#d9e2ec", timeVisible: true },
      crosshair: { mode: 1 }
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#1dbf73",
      downColor: "#f05d6f",
      borderUpColor: "#1dbf73",
      borderDownColor: "#f05d6f",
      wickUpColor: "#1dbf73",
      wickDownColor: "#f05d6f"
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceLineVisible: false,
      lastValueVisible: false
    }, 1);
    const movingAverageSeries = Object.fromEntries(
      MOVING_AVERAGES.map((average) => [
        average.key,
        chart.addSeries(LineSeries, {
          color: average.color,
          lineWidth: 2,
          crosshairMarkerVisible: false,
          lastValueVisible: false,
          priceLineVisible: false
        })
      ])
    ) as Record<MovingAverageKey, ISeriesApi<"Line">>;
    chartRef.current = chart;
    seriesRef.current = series;
    volumeSeriesRef.current = volumeSeries;
    movingAverageSeriesRef.current = movingAverageSeries;
    extremaMarkersRef.current = createSeriesMarkers(series, [], { autoScale: false });
    const resizeVolumePane = () => {
      const pane = chart.panes()[1];
      if (pane && chartContainer.current) pane.setHeight(Math.max(80, Math.round(chartContainer.current.clientHeight * 0.24)));
    };
    const volumeResizeObserver = new ResizeObserver(resizeVolumePane);
    volumeResizeObserver.observe(chartContainer.current);
    resizeVolumePane();
    const handleCrosshairMove: Parameters<IChartApi["subscribeCrosshairMove"]>[0] = (param) => {
      const nextTime = typeof param.time === "number" ? param.time : null;
      setHoveredCandleTime(nextTime);
    };
    const handleChartClick: Parameters<IChartApi["subscribeClick"]>[0] = (param) => {
      if (typeof param.time === "number") openCandleAtTimeRef.current(param.time);
    };
    const handleVisibleRangeChange = (range: LogicalRange | null) => {
      setVisibleLogicalRange(range);
    };
    chart.subscribeCrosshairMove(handleCrosshairMove);
    chart.subscribeClick(handleChartClick);
    chart.timeScale().subscribeVisibleLogicalRangeChange(handleVisibleRangeChange);
    return () => {
      volumeResizeObserver.disconnect();
      chart.unsubscribeCrosshairMove(handleCrosshairMove);
      chart.unsubscribeClick(handleChartClick);
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleVisibleRangeChange);
      extremaMarkersRef.current = null;
      movingAverageSeriesRef.current = null;
      seriesRef.current = null;
      volumeSeriesRef.current = null;
      chartRef.current = null;
      chart.remove();
    };
  }, []);

  React.useEffect(() => {
    setHoveredCandleTime(null);
    setVisibleLogicalRange(null);
    hasFittedChartRef.current = false;
    previousCandleCountRef.current = 0;
  }, [selected, bar]);

  React.useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    const averageSeries = movingAverageSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    if (!series || !averageSeries || !volumeSeries || !chart) return;
    const visibleRange = chart.timeScale().getVisibleLogicalRange();
    const wasViewingNewestEdge =
      visibleRange === null || visibleRange.to >= previousCandleCountRef.current - 1 - 2;
    series.setData(toCandleData(candles));
    volumeSeries.setData(toVolumeData(candles));
    MOVING_AVERAGES.forEach((average) => {
      averageSeries[average.key].setData(movingAverages.series[average.key]);
    });
    if (candles.length === 0) {
      previousCandleCountRef.current = 0;
      return;
    }
    if (!hasFittedChartRef.current) {
      chart.timeScale().fitContent();
      focusNewestCandleWindow(chart, candles.length);
      hasFittedChartRef.current = true;
    } else if (wasViewingNewestEdge) {
      chart.timeScale().scrollToRealTime();
    }
    previousCandleCountRef.current = candles.length;
  }, [candles, movingAverages]);

  React.useEffect(() => {
    extremaMarkersRef.current?.setMarkers(extremaMarkers(visibleExtrema));
  }, [visibleExtrema]);

  React.useEffect(() => {
    if (candleCloseCountdown(latestCandle, bar, Date.now()) === null) return;
    setChartClock(Date.now());
    const timer = window.setInterval(() => setChartClock(Date.now()), 1_000);
    return () => window.clearInterval(timer);
  }, [bar, latestCandle?.confirm, latestCandle?.ts]);

  const focusCurrentTrend = React.useCallback(() => {
    const chart = chartRef.current;
    if (!chart || candles.length === 0) return;
    focusNewestCandleWindow(chart, candles.length);
    setHoveredCandleTime(null);
  }, [candles.length]);

  return (
    <section className="marketMain marketChartMain">
      <div className="marketChartTopbar">
        <PageHeader eyebrow="实时行情" title="行情图表" actions={
          <div className="workspaceActions">
            <Button
              type="button"
              className="secondaryButton slim"
              onClick={() => onOpenAiOutlook?.(selected, bar)}
              title="AI看行情"
              variant="default"
              size="xs"
              leftSection={<BrainCircuit size={15} />}
            >
              AI看行情
            </Button>
          </div>
        } />

        <div className="marketChartToolbar" aria-label="图表工具栏">
          <div className="marketChartDataStatus" aria-label="行情数据状态">
            <div className="statusPills">
              <Badge className={`statusPill ${tickerRealtime.connected && tickerSource.includes("ws") ? "live" : "warning"}`} color={tickerRealtime.connected && tickerSource.includes("ws") ? "teal" : "yellow"} variant="light">
                价格 {sourceLabel(tickerSource)}
              </Badge>
              <Badge className={`statusPill ${candleStreamLive ? "live" : "warning"}`} color={candleStreamLive ? "teal" : "yellow"} variant="light">
                K线 {sourceLabel(candleSource)}
              </Badge>
            </div>
            {tickerFreshness ? <span className="marketChartFreshness" title={tickerFreshness.detail}>{tickerFreshness.pill}</span> : null}
            <span className="marketChartUpdateTime">
              更新 {(tickerUpdatedAt ?? lastPushedAt) ? new Date(tickerUpdatedAt ?? lastPushedAt ?? 0).toLocaleTimeString("zh-CN") : "--"}
            </span>
          </div>
          <div className="marketChartViewControls" aria-label="图表视图">
            <Button
              type="button"
              className="secondaryButton slim latestChartButton"
              onClick={focusCurrentTrend}
              disabled={candles.length === 0}
              title="聚焦最新 48 根K线"
              variant="default"
              size="xs"
            >
              最新
            </Button>
            <SegmentedControl
              className="bars"
              aria-label="K线周期"
              value={bar}
              onChange={setBar}
              data={bars}
              size="xs"
            />
          </div>
        </div>
      </div>

        <div className={`marketNoticeSlot ${visibleWarning ? "visible" : ""}`}>
          {visibleWarning ? <Notice tone="warning">{visibleWarning}</Notice> : null}
        </div>

        <Paper component="section" className="contractHero">
          <div className="contractTitle">
            <span className="eyebrow">选中合约</span>
            <h2>{selected}</h2>
            <div className="contractSubline">
              <span>{selectedInstrument?.inst_family ?? "SWAP"}</span>
              <span>{instrumentSettlementLabel(selectedInstrument, selected)}</span>
              <span>面值 {contractValueLabel(selectedInstrument, selected)}</span>
              <span className={`stateBadge ${selectedInstrument?.state === "live" ? "live" : ""}`}>
                {stateLabel(selectedInstrument?.state)}
              </span>
            </div>
          </div>
          <div className="heroPriceBlock">
            <span>最新价</span>
            {initialTickerLoading ? <DataLoadingState label="正在读取价格" compact /> : <><strong className={dayChangeClass}>{formatMarketNumber(livePrice)}</strong>
            <small
              className={dayChangeClass}
              title="今日涨跌（按 UTC+8 日开盘价计算）"
              aria-label={`今日涨跌（UTC+8） ${formatSigned(dayChange.absolute)}，${formatSignedPercent(dayChange.percent)}`}
            >
              {formatSigned(dayChange.absolute)} / {formatSignedPercent(dayChange.percent)}
            </small></>}
          </div>
          {initialTickerLoading ? <DataLoadingSkeleton variant="metrics" label="正在读取24小时行情摘要" /> : <div className="heroTiles" aria-label="24小时行情摘要">
            <MiniMetric label="24h 高" value={formatMarketNumber(selectedTicker?.high24h)} />
            <MiniMetric label="24h 低" value={formatMarketNumber(selectedTicker?.low24h)} />
            <MiniMetric label={activity24h.label} value={activity24h.value} />
          </div>}
        </Paper>

        <div className="marketChartReading">
        <Paper component="section" className="chartPanel" p={0}>
          <div className="chartHeader">
            <div>
              <strong>{selected}</strong>
              <span>{bar} K线 · {candles.length === 0 ? initialChartLoading ? "数据加载中" : "暂无K线数据" : candleStreamLive ? "实时推送" : "最近可用数据"}</span>
            </div>
            <div className="chartHeaderMeta">
              <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">
                TradingView
              </a>
              <Badge className={`statusPill ${candles.length === 0 ? "" : candleStreamLive ? "live" : "warning"}`} color={candles.length === 0 ? "gray" : candleStreamLive ? "teal" : "yellow"} variant="light">
                {candles.length === 0 ? "K线准备中" : candleStreamLive ? "K线实时" : isDegradedCandleSource(candleSource) ? "数据待补齐" : "K线回退"}
              </Badge>
            </div>
          </div>
          <div className="candleInspector" aria-label="K线检查器">
            <CandleInspectorMetric
              label={hoveredCandleTime === null ? "最新K线" : "查看K线"}
              value={formatTime(detailCandle?.ts)}
              featured
            />
            <CandleInspectorMetric label="收盘价" value={formatMarketNumber(detailCandle?.close)} />
            <CandleInspectorMetric label="涨跌幅" value={formatSignedPercent(detailCandlePercent)} valueClass={detailCandleDeltaClass} />
            <Button
              type="button"
              className="candleDetailButton"
              variant="default"
              size="compact-xs"
              disabled={!detailCandle}
              title={detailCandle ? "查看当前K线节点的完整数据" : "K线加载后可查看节点详情"}
              onClick={() => openCandleDetail(detailCandle)}
            >
              节点详情
            </Button>
          </div>
          <div className="chartArea">
            <div ref={chartContainer} className="chart" />
            {initialChartLoading ? <div className="chartLoadingOverlay"><DataLoadingState label={`正在读取 ${selected} · ${bar} K线`} /></div> : null}
            <div className="chartTrendLegend" aria-label="移动平均趋势">
              {MOVING_AVERAGES.map((average) => (
                <span key={average.key} style={{ color: average.color }}>
                  {average.label}: {trendLegendValues?.[average.key] === null || trendLegendValues?.[average.key] === undefined
                    ? "--"
                    : formatTrendNumber(trendLegendValues[average.key])}
                </span>
              ))}
              {visibleExtrema.high && visibleExtrema.low && String(visibleExtrema.high.ts) === String(visibleExtrema.low.ts) ? (
                <span className="chartRangeLegend neutral">
                  高低 {formatTrendNumber(visibleExtrema.high.high)} / {formatTrendNumber(visibleExtrema.low.low)}
                </span>
              ) : (
                <>
                  {visibleExtrema.high ? <span className="chartRangeLegend high">高 {formatTrendNumber(visibleExtrema.high.high)}</span> : null}
                  {visibleExtrema.low ? <span className="chartRangeLegend low">低 {formatTrendNumber(visibleExtrema.low.low)}</span> : null}
                </>
              )}
            </div>
            <div className="chartVolumeLegend" aria-label="K线成交量">
              {hasVolume ? `成交量（张） ${formatMarketNumber(detailCandle?.volume)}` : "成交量暂无数据"}
            </div>
            {formattedCandleCountdown ? (
              <span className="chartCountdownOverlay" aria-label={`距${bar}K线收线 ${formattedCandleCountdown}`}>
                距收线 {formattedCandleCountdown}
              </span>
            ) : null}
          </div>
          {chartLoading && candles.length > 0 ? <DataLoadingState label="K线快照更新中，正在保留当前图表" compact /> : null}
        </Paper>
        <MarketOrderBook instId={selected} />
        </div>
        <Modal
          opened={candleDetail !== null}
          onClose={() => setCandleDetail(null)}
          title="K线节点详情"
          centered
          size="lg"
          classNames={{ body: "candleDetailModalBody" }}
          closeButtonProps={{ "aria-label": "关闭K线节点详情" }}
        >
          {candleDetail ? <div className="candleDetailContent">
            <div className="candleDetailContext">
              <div>
                <strong>{candleDetail.instId}</strong>
                <span>{candleDetail.bar} K线 · {formatTime(candleDetail.candle.ts)}</span>
              </div>
              <Badge color={candleDetail.candle.confirm === "1" ? "gray" : "teal"} variant="light">
                {candleStateLabel(candleDetail.candle)}
              </Badge>
            </div>
            <section className="candleDetailSection" aria-label="节点价格">
              <h3>价格</h3>
              <div className="candleDetailGrid">
                <CandleInspectorMetric label="开盘价" value={formatMarketNumber(candleDetail.candle.open)} />
                <CandleInspectorMetric label="最高价" value={formatMarketNumber(candleDetail.candle.high)} />
                <CandleInspectorMetric label="最低价" value={formatMarketNumber(candleDetail.candle.low)} />
                <CandleInspectorMetric label="收盘价" value={formatMarketNumber(candleDetail.candle.close)} />
              </div>
            </section>
            <section className="candleDetailSection" aria-label="节点变化与成交">
              <h3>变化与成交</h3>
              <div className="candleDetailGrid">
                <CandleInspectorMetric label="涨跌额" value={formatSigned(selectedCandleDelta.absolute)} valueClass={changeClass(selectedCandleDelta.absolute)} />
                <CandleInspectorMetric label="涨跌幅" value={formatSignedPercent(selectedCandlePercent)} valueClass={selectedCandlePercent === 0 ? "" : changeClass(selectedCandlePercent)} />
                <CandleInspectorMetric label="振幅" value={selectedCandleAmplitude === null ? "--" : `${selectedCandleAmplitude.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}%`} />
                <CandleInspectorMetric label="成交量（张）" value={formatMarketNumber(candleDetail.candle.volume)} />
                {candleDetail.candle.volumeQuote ? <CandleInspectorMetric label="成交额" value={formatMarketNumber(candleDetail.candle.volumeQuote)} /> : null}
              </div>
            </section>
            <section className="candleDetailSection" aria-label="节点均线">
              <h3>均线</h3>
              <div className="candleDetailGrid">
                {MOVING_AVERAGES.map((average) => <CandleInspectorMetric
                  key={average.key}
                  label={average.label}
                  value={candleDetail.averages?.[average.key] === null || candleDetail.averages?.[average.key] === undefined
                    ? "--"
                    : formatTrendNumber(candleDetail.averages[average.key])}
                />)}
              </div>
            </section>
            <p className="candleDetailFootnote">
              涨跌以前一根K线收盘价为基准{candleDetail.previous ? "" : "；首根K线以本根开盘价为基准"}。数据来源：{sourceLabel(candleDetail.source)}。以上为打开详情时的图表快照。
              {!candleDetail.candle.volumeQuote ? " 当前数据源未提供该节点成交额。" : ""}
            </p>
          </div> : null}
        </Modal>
    </section>
  );
}

function MarketAiRecordsPage() {
  const [contractInput, setContractInput] = React.useState("");
  const [contractFilter, setContractFilter] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("");
  const [kindFilter, setKindFilter] = React.useState("price_plan_15m");
  const [pricedOnly, setPricedOnly] = React.useState(true);
  const [page, setPage] = React.useState(0);
  const [refreshKey, setRefreshKey] = React.useState(0);
  const [result, setResult] = React.useState<{ key: string; data: MarketAiVerificationRecords } | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [filterError, setFilterError] = React.useState("");
  const pageSize = 20;
  const queryKey = `${contractFilter}|${statusFilter}|${kindFilter}|${pricedOnly}|${page}`;

  React.useEffect(() => {
    let active = true;
    const readRecords = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ limit: String(pageSize), offset: String(page * pageSize) });
        if (contractFilter) params.set("instId", contractFilter);
        if (statusFilter) params.set("status", statusFilter);
        if (kindFilter) params.set("kind", kindFilter);
        if (pricedOnly) params.set("pricedOnly", "true");
        const response = await fetch(`${API_BASE}/api/market/ai-outlook/evaluations/records?${params}`);
        if (!response.ok) throw new Error("records unavailable");
        const data = (await response.json()) as MarketAiVerificationRecords;
        if (active) { setResult({ key: queryKey, data }); setError(false); }
      } catch {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    };
    void readRecords();
    return () => { active = false; };
  }, [contractFilter, statusFilter, kindFilter, pricedOnly, page, refreshKey, queryKey]);

  const current = result?.key === queryKey ? result.data : null;
  const statusLabels: Record<string, string> = {
    pending: "待验证", hit: "方向符合", miss: "方向未符", flat: "波动不足",
    not_scored: "不计分", insufficient_data: "数据不足"
  };
  const touchLabel = (value?: boolean | null) => value === true ? "触及" : value === false ? "未触及" : "未记录";
  const formatRecordTime = (value?: number | null) => value ? new Date(value).toLocaleString("zh-CN") : "未记录";
  const applyContractFilter = (event: React.FormEvent) => {
    event.preventDefault();
    const value = contractInput.trim().toUpperCase();
    if (value && !/^[A-Z0-9]+-[A-Z0-9]+-SWAP$/.test(value)) {
      setFilterError("请输入完整永续合约代码，例如 ETH-USDT-SWAP。");
      return;
    }
    setFilterError("");
    setPage(0);
    setContractFilter(value);
  };

  return (
    <section className="marketAiRecordsPage" aria-label="AI预测记录管理">
      <div className="workspaceHeader marketAiRecordsHeader">
        <div>
          <span className="eyebrow">AI看行情</span>
          <h1>预测记录</h1>
          <p>集中查看历史预测的目标 K 线时段、买卖参考价、方向核验和触价观察。</p>
        </div>
        <Button type="button" variant="default" size="xs" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading} leftSection={<RefreshCw size={15} />}>
          {loading ? "更新中" : "刷新记录"}
        </Button>
      </div>
      <Paper component="section" className="marketAiRecordsContent" aria-label="预测记录列表">
        <form className="marketAiRecordsFilters" onSubmit={applyContractFilter}>
          <TextInput label="合约代码" placeholder="全部合约，例如 ETH-USDT-SWAP" value={contractInput} onChange={(event) => setContractInput(event.target.value)} size="xs" />
          <Button type="submit" variant="default" size="xs">筛选合约</Button>
          <Select label="预测类型" value={kindFilter || "all"} onChange={(value) => { setKindFilter(value === "all" ? "" : value ?? ""); setPricedOnly(false); setPage(0); }} data={[{ value: "all", label: "全部类型" }, { value: "main_direction", label: "主图方向" }, { value: "price_plan_15m", label: "15分钟价格计划" }]} allowDeselect={false} size="xs" />
          <Select label="核验结果" value={statusFilter || "all"} onChange={(value) => { setStatusFilter(value === "all" ? "" : value ?? ""); setPage(0); }} data={[{ value: "all", label: "全部结果" }, { value: "pending", label: "待验证" }, { value: "hit", label: "方向符合" }, { value: "miss", label: "方向未符" }, { value: "flat", label: "波动不足" }, { value: "not_scored", label: "不计分" }, { value: "insufficient_data", label: "数据不足" }]} allowDeselect={false} size="xs" />
          {kindFilter === "price_plan_15m" ? <Checkbox className="marketAiRecordsPricedFilter" label="只看有买卖价的计划" checked={pricedOnly} onChange={(event) => { setPricedOnly(event.target.checked); setPage(0); }} /> : null}
        </form>
        {filterError ? <p className="marketAiVerificationMessage" role="alert">{filterError}</p> : null}
        <div className="marketAiRecordsCount" role="status">
          {current ? `共 ${current.total} 条预测样本 · 第 ${page + 1} 页` : loading ? "正在读取预测记录" : "预测记录暂不可用"}
          {loading && current ? " · 更新中" : ""}
        </div>
        {error ? <Notice tone="danger">预测记录暂时无法更新。请点击“刷新记录”重试。{current ? "当前仍显示上次结果。" : ""}</Notice> : null}
        {loading && !current ? <DataLoadingState label="正在读取预测记录" /> : null}
        {current && !current.samples.length ? <p className="marketAiRecordsEmpty">当前筛选条件下没有记录。{pricedOnly ? "可取消“只看有买卖价的计划”查看无价格样本。" : "分析报告生成后，预测样本会自动保存在这里。"}</p> : null}
        {current?.samples.length ? <div className="marketAiRecordsList">
          {current.samples.map((sample) => {
            const planDeadline = sample.planValidUntil || sample.dueAt;
            const isPricePlan = sample.kind === "price_plan_15m";
            const exitAction = sample.direction === "long" ? "卖出平多" : "买回平空";
            const hypotheticalReturn = marketAiHypotheticalReturn(sample.hypotheticalCloseReturnPct);
            const entryState = marketAiPlanEntryState(sample);
            return <article className={`marketAiRecord ${isPricePlan ? `${sample.direction} ${sample.planStatus || ""}` : ""}`} key={sample.id}>
            <div className="marketAiRecordHeader">
              <div>
                <strong>{sample.instId} · {sample.kind === "price_plan_15m" ? "15分钟价格计划" : "主图方向"}</strong>
                <small>预测生成 {formatRecordTime(sample.createdAt)} · {sample.bar} · {sample.direction === "long" ? "预测做多" : sample.direction === "short" ? "预测做空" : "无方向"}</small>
              </div>
              <span className={`marketAiVerificationStatus ${isPricePlan ? entryState.tone : sample.status}`}>{isPricePlan ? entryState.label : statusLabels[sample.status] || "待核验"}</span>
            </div>
            {isPricePlan && sample.entryPrice && sample.targetPrice && sample.stopPrice ? <div className="marketAiRecordPlan" aria-label="原预测买卖计划">
              <strong>{sample.entryBasis === "quote_snapshot" ? "分析时报价与预测目标" : sample.planStatus === "watch" ? "旧计划候选条件 · 当时尚未确认全部入场条件" : "旧突破价格计划"}</strong>
              <div className="marketAiRecordPlanWindow"><span>{sample.entryBasis === "quote_snapshot" ? "报价记录" : sample.planStatus === "watch" ? "条件观察开始" : "入场观察开始"} <b>{formatRecordTime(sample.entryBasis === "quote_snapshot" && sample.entryQuoteTs ? sample.entryQuoteTs : sample.createdAt)}</b></span><span>{sample.planStatus === "watch" && sample.entryBasis !== "quote_snapshot" ? "本轮条件复核" : "目标核验截止"} <b>{formatRecordTime(planDeadline)}</b></span></div>
              {sample.planStatus === "watch" && sample.createdAt < planDeadline ? <p className="marketAiRecordPlanWatchNote">{marketAiWatchConditionNote(sample.priceConditionMet, sample.entryBasis)}</p> : null}
              {sample.createdAt < planDeadline ? <>
                <div className="marketAiRecordPlanPrices">
                  <div className="marketAiRecordPlanEntry"><span>{sample.entryBasis === "quote_snapshot" ? sample.direction === "long" ? "分析时卖一价 · 预计做多买入" : "分析时买一价 · 预计做空卖出" : `${sample.planStatus === "watch" ? "旧计划候选入场价" : "旧计划预计入场价"} · ${sample.direction === "long" ? "做多买入" : "做空卖出"}`}</span><strong>{sample.entryPrice}</strong><small>{sample.entryBasis === "quote_snapshot" ? "报价已记录 · 成交未证实" : sample.planStatus === "watch" ? marketAiWatchEntryLabel(sample.priceConditionMet, sample.entryBasis) : "观察期内按条件参考"}</small></div>
                  <div><span>预测止盈价 · {exitAction}</span><strong>{sample.targetPrice}</strong><small>{marketAiPlannedTargetMove(sample.entryPrice, sample.targetPrice, sample.direction)} · {marketAiTargetState(sample)}</small></div>
                  <div><span>若已入场 · 止损 {exitAction}</span><strong>{sample.stopPrice}</strong><small>未入场时不生效</small></div>
                </div>
                <p>{sample.entryBasis === "quote_snapshot" ? "预计入场价取当时报价；止盈到价仅验证价格路径，无法证明实际成交或盈利。" : "止盈和止损是入场后不同的退出情形；当前记录无法证明实际入场、退出时间或成交价。"}</p>
                {sample.priceLogic ? <Disclosure className="marketAiRecordLogicDisclosure" label="查看这组价格的计算依据"><MarketAiPriceLogicDetails logic={sample.priceLogic} compact /></Disclosure> : <p className="marketAiRecordLogicMissing">该历史记录未保存完整的方向、报价和 K 线极值，无法补写准确的计算明细。</p>}
              </> : <p><b>已过期</b>报告生成于 {formatRecordTime(sample.createdAt)}，计划截止于 {formatRecordTime(planDeadline)}，没有有效入场或退出时段。原参考价：{sample.direction === "long" ? "做多买入" : "做空卖出"} <em>{sample.entryPrice}</em>，止盈 <em>{sample.targetPrice}</em>，止损 <em>{sample.stopPrice}</em>。</p>}
              {sample.planCondition ? <p><b>入场条件</b>{sample.planCondition}</p> : null}
            </div> : null}
            <div className="marketAiRecordResult" aria-label="后续验证结果">
              <div className="marketAiRecordResultHeader"><strong>后续验证结果</strong><span>{sample.evaluatedAt ? `核验于 ${formatRecordTime(sample.evaluatedAt)}` : sample.status === "pending" ? `预计 ${formatRecordTime(sample.dueAt)} 后` : "未核验"}</span></div>
              {isPricePlan && sample.targetPrice ? <div className="marketAiRecordTargetResult">
                <span>预测止盈价 {sample.targetPrice} · 到价核验</span>
                <strong>{marketAiTargetState(sample)}</strong>
                {sample.targetObservedAt ? <small>首次到价分钟：{formatRecordTime(sample.targetObservedAt)}（仅 1 分钟 K 线，无法确定具体成交时刻）</small> : null}
                <small>{marketAiTargetSequence(sample)}</small>
                {sample.pricePathStartsAt && sample.pricePathEndsAt ? <small>核对 {formatRecordTime(sample.pricePathStartsAt)} ～ {formatRecordTime(sample.pricePathEndsAt)} 的完整 1 分钟 K 线{sample.pricePathReportMinuteExcluded ? "；报告生成所在分钟因无法区分前后，未计入" : ""}。</small> : null}
              </div> : null}
              {isPricePlan ? <div className={`marketAiRecordReturn ${sample.status === "pending" ? "pending" : "unconfirmed"}`}>
                <span>交易收益率</span>
                <strong>{sample.status === "pending" ? "待核验" : sample.entryBasis === "quote_snapshot" ? "成交未证实 · 不适用" : marketAiEntryNotObserved(sample) ? "未观察到入场 · 不适用" : sample.entryReachedAfterReport === true || sample.entryReferenceTouched === true ? "成交未证实 · 不适用" : "入场未确认 · 不适用"}</strong>
                {hypotheticalReturn ? <b className={`marketAiPriceComparison ${hypotheticalReturn.tone}`}>{hypotheticalReturn.label} · 仅作价格对照</b> : null}
                <small>{marketAiHypotheticalReturnNote(sample)}</small>
              </div> : null}
              <div className="marketAiRecordFacts">
                <span>{isPricePlan ? "行情收盘方向" : "方向结果"} <b className={`marketAiVerificationStatus ${sample.status}`}>{statusLabels[sample.status] || "待核验"}</b></span>
                {isPricePlan ? <span>{sample.entryBasis === "quote_snapshot" ? "分析时报价" : "旧计划入场价"} <b>{sample.status === "not_scored" ? "不适用" : marketAiPlanEntryState(sample).label}</b></span> : <span>买卖计划 <b>本类样本只核验方向</b></span>}
                {isPricePlan ? <span>{sample.entryBasis === "quote_snapshot" ? "报价后止盈路径" : "入场后止盈路径"} <b>{sample.targetAfterEntryObserved === true ? sample.entryBasis === "quote_snapshot" ? "报价后目标到价" : "先入场后到价" : sample.targetAfterEntryObserved === false ? "未观察到" : "无法确认先后"}</b></span> : null}
                {isPricePlan ? <span>止损参考价 <b>{sample.entryBasis === "quote_snapshot" ? sample.status === "pending" ? "待验证" : touchLabel(sample.stopReferenceTouched) : marketAiEntryNotObserved(sample) ? "未观察到入场 · 不生效" : sample.status === "not_scored" ? "不适用" : sample.status === "pending" ? "待验证" : touchLabel(sample.stopReferenceTouched)}</b></span> : null}
              </div>
              <p>{isPricePlan ? "行情方向核验：目标" : "目标"} {sample.bar} K 线 {sample.targetTs ? `${formatRecordTime(sample.targetTs)} ～ ${formatRecordTime(sample.dueAt)}` : "未记录"} · 基准收盘 {sample.baselineClose || "--"} → 实际收盘 {sample.observedClose || (sample.status === "pending" ? "待验证" : sample.status === "not_scored" ? "不适用" : "未取得")}</p>
            </div>
            {sample.targetTs && sample.createdAt > sample.targetTs && sample.createdAt < sample.dueAt ? <p className="marketAiRecordTimingNote">报告生成时，这根目标 K 线已开始；核验涵盖生成前的部分走势。</p> : null}
            {sample.status === "not_scored" && sample.unscoredReason ? <p className="marketAiRecordTimingNote">不计分原因：{sample.unscoredReason}</p> : null}
            {isPricePlan && marketAiEntryNotObserved(sample) ? <p className="marketAiRecordVerifiedAt">可核对时段内未观察到入场参考价，没有可核对的先入场后退出路径。</p> : null}
            {isPricePlan && !sample.pricePathCoverage && sample.entryReferenceTouched === true && (sample.targetReferenceTouched || sample.stopReferenceTouched) ? <p className="marketAiRecordVerifiedAt">旧记录的参考价曾在目标 K 线内触及；15分钟 K 线无法确认入场和退出的先后，不计为完成交易。</p> : null}
            <Disclosure className="marketAiRecordDisclosure" label={<span>查看预测与核验明细</span>}>
              <div className="marketAiRecordDetails">
                <p><b>报告原文摘要</b>{sample.reportSummary || "未保存摘要"}</p>
                <p><b>记录编号</b>{sample.id}</p>
                <p><b>报告编号</b>{sample.reportId}</p>
                <p><b>核验时间</b>{sample.evaluatedAt ? formatRecordTime(sample.evaluatedAt) : sample.status === "pending" ? `预计 ${formatRecordTime(sample.dueAt)} 后` : "未核验"}</p>
                {sample.movePct ? <p><b>收盘变化</b>{sample.movePct}% · 方向判定门槛 {sample.thresholdPct}%</p> : null}
                {isPricePlan ? <p><b>价格计划</b>{sample.direction === "long" ? "做多买入" : sample.direction === "short" ? "做空卖出" : "买卖"}参考价 {sample.entryPrice || "--"} · 止盈 {sample.targetPrice || "--"} · 止损 {sample.stopPrice || "--"} · 截止 {formatRecordTime(planDeadline)}</p> : null}
                {sample.kind === "price_plan_15m" && sample.entryReferenceTouched !== null && sample.entryReferenceTouched !== undefined ? <p><b>触价观察</b>买卖 {touchLabel(sample.entryReferenceTouched)} · 止损 {touchLabel(sample.stopReferenceTouched)} · 止盈 {touchLabel(sample.targetReferenceTouched)}；无法判断先后，不代表成交。</p> : null}
                {sample.unscoredReason ? <p><b>不计分原因</b>{sample.unscoredReason}</p> : null}
                <p><b>来源与版本</b>{sourceLabel(sample.reportSource)} · {sample.promptVersion || "--"}</p>
              </div>
            </Disclosure>
          </article>;})}
        </div> : null}
        {current && current.total > pageSize ? <div className="marketAiRecordsPagination">
          <Button type="button" variant="default" size="xs" disabled={page === 0 || loading} onClick={() => setPage((value) => Math.max(0, value - 1))}>上一页</Button>
          <span>{page + 1} / {Math.ceil(current.total / pageSize)}</span>
          <Button type="button" variant="default" size="xs" disabled={(page + 1) * pageSize >= current.total || loading} onClick={() => setPage((value) => value + 1)}>下一页</Button>
        </div> : null}
        <small className="marketAiVerificationScope">{current?.scope || "方向核验与参考价触及仅供回看，不代表成交或收益。"}</small>
      </Paper>
    </section>
  );
}

function MarketAiOutlookPage({
  initialBar = "1m",
  onOpenChart
}: {
  initialBar?: string;
  onOpenChart?: (instId: string, bar: string) => void;
}) {
  const {
    selected, instruments, tickers, tickersLoading, tickerUpdatedAt, tickerRefresh, tickerRealtime, warning: workspaceWarning,
    chartBar: bar, setChartBar, chartLoading, chartSnapshot, chartUpdatedAt, refreshChartSnapshot
  } = useMarketContractWorkspace();
  const [aiOutlook, setAiOutlook] = React.useState<MarketAiOutlookResponse | null>(null);
  const [aiOutlookLoading, setAiOutlookLoading] = React.useState(false);
  const [aiOutlookError, setAiOutlookError] = React.useState("");

  React.useEffect(() => {
    setAiOutlook(null);
    setAiOutlookError("");
  }, [bar, selected]);

  React.useEffect(() => {
    const normalized = normalizeRouteBar(initialBar);
    if (normalized !== bar) {
      setChartBar(normalized);
    }
  }, [bar, initialBar, setChartBar]);

  const selectedInstrument = React.useMemo(
    () => instruments.find((item) => item.inst_id === selected),
    [instruments, selected]
  );
  const selectedTicker = tickers[selected] ?? null;
  const dayChange = tickerTodayChange(selectedTicker);
  const turnover24h = tickerValue(selectedTicker, ["volCcyQuote24h", "volCcy24h", "vol24h"]);
  const tickerFreshness = tickerRefreshStatus(tickerRefresh, tickerRealtime.connected);
  const chartHasNewerSnapshot = Boolean(
    aiOutlook?.chartSnapshot?.snapshotId && chartSnapshot?.snapshotId && aiOutlook.chartSnapshot.snapshotId !== chartSnapshot.snapshotId
  );
  const analysisAvailable = Boolean(chartSnapshot?.snapshotId);
  const initialTickerLoading = tickersLoading && Object.keys(tickers).length === 0;

  const loadAiOutlook = React.useCallback(
    async (options?: { forceAnalysis?: boolean; forceMacro?: boolean }) => {
      setAiOutlookLoading(true);
      setAiOutlookError("");
      try {
        if (!chartSnapshot?.snapshotId) {
          throw new Error("当前图表快照仍在加载，请等待 K线数据就绪后再分析。");
        }
        let activeSnapshot: ChartSnapshotMetadata | null = chartSnapshot;
        if (!chartSnapshotFreshForAnalysis(activeSnapshot)) {
          activeSnapshot = await refreshChartSnapshot(true);
        }
        if (!chartSnapshotFreshForAnalysis(activeSnapshot)) {
          throw new Error("当前主图 K线尚未更新，请稍后重新分析。");
        }
        const requestOutlook = async (snapshotId: string): Promise<MarketAiOutlookResponse> => {
          const response = await fetch(`${API_BASE}/api/market/ai-outlook`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              instId: selected,
              bar,
              limit: 120,
              snapshotId,
              forceAnalysis: Boolean(options?.forceAnalysis),
              forceMacro: Boolean(options?.forceMacro)
            })
          });
          if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(String(payload.detail || "AI看行情加载失败"));
          }
          return (await response.json()) as MarketAiOutlookResponse;
        };
        let payload = await requestOutlook(activeSnapshot!.snapshotId);
        if (payload.snapshotRequired) {
          activeSnapshot = await refreshChartSnapshot(true);
          if (!chartSnapshotFreshForAnalysis(activeSnapshot)) {
            throw new Error("当前主图 K线尚未更新，请稍后重新分析。");
          }
          payload = await requestOutlook(activeSnapshot!.snapshotId);
        }
        if (payload.snapshotRequired) {
          throw new Error(payload.detail || "图表快照已失效，请等待图表重新加载后再分析。");
        }
        setAiOutlook(payload);
      } catch (error) {
        setAiOutlookError(error instanceof Error ? error.message : "AI看行情加载失败");
      } finally {
        setAiOutlookLoading(false);
      }
    },
    [bar, chartSnapshot, refreshChartSnapshot, selected]
  );

  const selectBar = (value: string) => {
    const normalized = normalizeRouteBar(value);
    setChartBar(normalized);
  };

  return (
    <section className="marketMain marketAiMain">
        <div className="workspaceHeader marketAiWorkspaceHeader">
          <div className="marketAiWorkspaceTitle">
            <span className="eyebrow">AI行情报告</span>
            <h1>AI看行情</h1>
            <p>{selected} · 主图观察 {bar} K线 · 一次分析自动读取 15分钟 / 1小时 / 日线</p>
          </div>
          <div className="workspaceActions marketAiWorkspaceActions">
            <Button
              type="button"
              className="secondaryButton slim"
              onClick={() => onOpenChart?.(selected, bar)}
              title="返回行情图表"
              variant="default"
              size="xs"
              leftSection={<ChartCandlestick size={15} />}
            >
              行情图表
            </Button>
            <div className="statusPills" aria-label="AI行情状态">
              <Badge className={`statusPill ${tickerRealtime.connected ? "live" : "warning"}`} color={tickerRealtime.connected ? "teal" : "yellow"} variant="light">
                {tickerRealtime.connected ? "价格实时" : "价格REST回退"}
              </Badge>
              {tickerFreshness ? <Badge className="statusPill warning" color="yellow" variant="light" title={tickerFreshness.detail}>{tickerFreshness.pill}</Badge> : null}
              <Badge className="statusPill" color="gray" variant="light">
                价格更新 {tickerUpdatedAt ? new Date(tickerUpdatedAt).toLocaleTimeString("zh-CN") : "--"}
              </Badge>
            </div>
            <div className="marketAiBarControl">
              <span>主图观察周期</span>
              <SegmentedControl
                className="bars"
                aria-label="主图观察周期"
                value={bar}
                onChange={selectBar}
                data={bars}
                size="xs"
              />
              <small>决定下一份报告主结论 · 切换后需重新分析</small>
            </div>
          </div>
        </div>

        {workspaceWarning ? <Notice tone="warning">{workspaceWarning}</Notice> : null}

        <Paper component="section" className="contractHero marketAiHero">
          <div className="contractTitle">
            <span className="eyebrow">当前报告合约</span>
            <h2>{selected}</h2>
            <div className="contractSubline">
              <span>{selectedInstrument?.inst_family ?? "SWAP"}</span>
              <span>{instrumentSettlementLabel(selectedInstrument, selected)}</span>
              <span>面值 {contractValueLabel(selectedInstrument, selected)}</span>
              <span className={`stateBadge ${selectedInstrument?.state === "live" ? "live" : ""}`}>
                {stateLabel(selectedInstrument?.state)}
              </span>
            </div>
          </div>
          <div className="heroPriceBlock">
            <span>最新价</span>
            {initialTickerLoading ? <DataLoadingState label="正在读取价格" compact /> : <><strong className={changeClass(dayChange.percent)}>{formatMarketNumber(selectedTicker?.last)}</strong>
            <small
              className={changeClass(dayChange.percent)}
              title="今日涨跌（按 UTC+8 日开盘价计算）"
              aria-label={`今日涨跌 ${formatSigned(dayChange.absolute)}，${formatSignedPercent(dayChange.percent)}`}
            >
              {formatSigned(dayChange.absolute)} / {formatSignedPercent(dayChange.percent)}
            </small></>}
          </div>
          {initialTickerLoading ? <DataLoadingSkeleton variant="metrics" label="正在读取24小时行情摘要" /> : <div className="heroTiles">
            <MiniMetric label="24h 高" value={formatMarketNumber(selectedTicker?.high24h)} />
            <MiniMetric label="24h 低" value={formatMarketNumber(selectedTicker?.low24h)} />
            <MiniMetric label="24h 量" value={formatCompact(turnover24h)} />
            <MiniMetric label="主图周期" value={bar} />
            <MiniMetric
              label="图表快照"
              value={chartSnapshot ? `${chartSnapshot.candleCount}根 · ${new Date(chartSnapshot.lastCandleTs || chartUpdatedAt || 0).toLocaleTimeString("zh-CN")}` : "加载中"}
            />
          </div>}
        </Paper>

        <MarketAiOutlookPanel
          selected={selected}
          outlook={aiOutlook}
          chartSnapshot={chartSnapshot}
          chartHasNewerSnapshot={chartHasNewerSnapshot}
          loading={aiOutlookLoading}
          analysisAvailable={analysisAvailable}
          snapshotLoading={chartLoading}
          error={aiOutlookError}
          onRefresh={() => loadAiOutlook({ forceAnalysis: Boolean(aiOutlook) })}
          fullPage
        />
    </section>
  );
}

function MarketStatsPage() {
  const { selected, instruments, tickers, tickersLoading, tickerUpdatedAt, tickerRefresh, tickerRealtime, warning: workspaceWarning } = useMarketContractWorkspace();
  const [statsPeriod, setStatsPeriod] = React.useState("5m");
  const stats = useMarketStats(selected, statsPeriod);

  const selectedInstrument = React.useMemo(
    () => instruments.find((item) => item.inst_id === selected),
    [instruments, selected]
  );
  const selectedTicker = tickers[selected] ?? null;
  const dayChange = tickerTodayChange(selectedTicker);
  const turnover24h = tickerValue(selectedTicker, ["volCcyQuote24h", "volCcy24h", "vol24h"]);
  const tickerFreshness = tickerRefreshStatus(tickerRefresh, tickerRealtime.connected);
  const initialTickerLoading = tickersLoading && Object.keys(tickers).length === 0;
  React.useEffect(() => {
    const scheduleNextRefresh = () =>
      window.setTimeout(() => {
        if (!document.hidden) {
          stats.reload({ force: true });
        }
        timer = scheduleNextRefresh();
      }, nextMarketStatsRefreshDelay(statsPeriod));

    let timer = scheduleNextRefresh();
    return () => window.clearTimeout(timer);
  }, [stats.reload, statsPeriod]);

  return (
    <section className="marketMain tradingDataMain">
        <PageHeader eyebrow="合约交易数据" title="交易数据" description={`${selected} · OKX Trading Statistics`} actions={
          <div className="workspaceActions">
            <div className="statusPills" aria-label="交易数据状态">
              <Badge className={`statusPill ${tickerRealtime.connected ? "live" : "warning"}`} color={tickerRealtime.connected ? "teal" : "yellow"} variant="light">
                {tickerRealtime.connected ? "价格实时" : "价格REST回退"}
              </Badge>
              {tickerFreshness ? <Badge className="statusPill warning" color="yellow" variant="light" title={tickerFreshness.detail}>{tickerFreshness.pill}</Badge> : null}
              <Badge className={`statusPill ${stats.statsWarnings.length ? "warning" : "live"}`} color={stats.statsWarnings.length ? "yellow" : "teal"} variant="light">
                {stats.marketStatsLoading
                  ? (stats.marketStats ? "统计更新中" : "统计加载中")
                  : `统计${stats.displayedStatsPeriod}${sourceLabel(stats.marketStats?.source)}`}
              </Badge>
              <Badge className="statusPill" color="gray" variant="light">
                价格更新 {tickerUpdatedAt ? new Date(tickerUpdatedAt).toLocaleTimeString("zh-CN") : "--"}
              </Badge>
            </div>
            <SegmentedControl
              className="bars"
              aria-label="统计周期"
              value={statsPeriod}
              onChange={setStatsPeriod}
              data={marketStatsBars}
              size="xs"
            />
          </div>
        } />

        {workspaceWarning ? <Notice tone="warning">{workspaceWarning}</Notice> : null}

        <Paper component="section" className="contractHero tradingDataHero">
          <div className="contractTitle">
            <span className="eyebrow">当前合约</span>
            <h2>{selected}</h2>
            <div className="contractSubline">
              <span>{selectedInstrument?.inst_family ?? "SWAP"}</span>
              <span>{instrumentSettlementLabel(selectedInstrument, selected)}</span>
              <span>面值 {contractValueLabel(selectedInstrument, selected)}</span>
              <span className={`stateBadge ${selectedInstrument?.state === "live" ? "live" : ""}`}>
                {stateLabel(selectedInstrument?.state)}
              </span>
            </div>
          </div>
          <div className="heroPriceBlock">
            <span>最新价</span>
            {initialTickerLoading ? <DataLoadingState label="正在读取价格" compact /> : <><strong className={changeClass(dayChange.percent)}>{formatMarketNumber(selectedTicker?.last)}</strong>
            <small
              className={changeClass(dayChange.percent)}
              title="今日涨跌（按 UTC+8 日开盘价计算）"
              aria-label={`今日涨跌 ${formatSigned(dayChange.absolute)}，${formatSignedPercent(dayChange.percent)}`}
            >
              {formatSigned(dayChange.absolute)} / {formatSignedPercent(dayChange.percent)}
            </small></>}
          </div>
          {initialTickerLoading ? <DataLoadingSkeleton variant="metrics" label="正在读取24小时行情摘要" /> : <div className="heroTiles">
            <MiniMetric label="24h 高" value={formatMarketNumber(selectedTicker?.high24h)} />
            <MiniMetric label="24h 低" value={formatMarketNumber(selectedTicker?.low24h)} />
            <MiniMetric label="24h 量" value={formatCompact(turnover24h)} />
            <MiniMetric label="统计周期" value={stats.displayedStatsPeriod} />
            <MiniMetric label="更新时间" value={stats.statsUpdatedAt} />
          </div>}
        </Paper>

        <TradingStatsSummary
          selected={selected}
          stats={stats}
          action={
            <Button
              type="button"
              className="secondaryButton slim tradingStatsAction"
              onClick={() => {
                window.location.hash = `#/market/chart?inst=${encodeURIComponent(selected)}`;
              }}
              variant="default"
              size="xs"
              leftSection={<ChartCandlestick size={15} />}
            >
              返回行情图表
            </Button>
          }
        />

        <TradingStatsDetails stats={stats} />
    </section>
  );
}

function TradingPage({
  initialInstId = "BTC-USDT-SWAP",
  onOpenOrders
}: {
  initialInstId?: string;
  onOpenOrders?: () => void;
}) {
  const confirmAction = useConfirmAction();
  const [settings, setSettings] = React.useState<SettingsStatus | null>(null);
  const [tradingAccount, setTradingAccount] = React.useState<AccountResponse | null>(null);
  const [instruments, setInstruments] = React.useState<Instrument[]>([]);
  const [tickers, setTickers] = React.useState<Record<string, Ticker>>({});
  const [leverageRows, setLeverageRows] = React.useState<LeverageInfo[]>([]);
  const [instId, setInstId] = React.useState(initialInstId);
  const [contractSearch, setContractSearch] = React.useState("");
  const [contractFilter, setContractFilter] = React.useState<InstrumentFilter>("live");
  const [instrumentPickerOpen, setInstrumentPickerOpen] = React.useState(false);
  const [tdMode, setTdMode] = React.useState("cross");
  const [side, setSide] = React.useState("buy");
  const [ordType, setOrdType] = React.useState("limit");
  const [px, setPx] = React.useState("");
  const [sz, setSz] = React.useState("");
  const [quantityUnit, setQuantityUnit] = React.useState<QuantityUnit>("contracts");
  const [reduceOnly, setReduceOnly] = React.useState(false);
  const [leverageInput, setLeverageInput] = React.useState("");
  const [leverageDirty, setLeverageDirty] = React.useState(false);
  const [leverageLoading, setLeverageLoading] = React.useState(false);
  const posSide = posSideForTradeOrder(side, reduceOnly);
  const tradeDirectionOptions = reduceOnly ? reduceOnlySideOptions : sideOptions;
  const [showAdvancedOrderTypes, setShowAdvancedOrderTypes] = React.useState(false);
  // 初始不占用「加载中」状态：账户概览条已表达连接状态，底部再挂一行加载提示只会白占高度、
  // 把下单面板的提交按钮挤出视口。数据到达后由各实时/轮询回调写入具体状态。
  const [status, setStatus] = React.useState("");
  const [warning, setWarning] = React.useState("");
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const [applyingLeverage, setApplyingLeverage] = React.useState(false);
  const instrumentPickerRef = React.useRef<HTMLDivElement | null>(null);
  const accountLoadingRef = React.useRef(false);
  const accountRequestSeqRef = React.useRef(0);
  const accountLastFetchRef = React.useRef(0);
  const leverageLoadingRef = React.useRef(false);
  const leverageRequestSeqRef = React.useRef(0);
  const pendingClOrdIdRef = React.useRef<string>("");

  // 交易工作台：挂单/持仓就地视图与操作
  const [pendingOrders, setPendingOrders] = React.useState<PendingOrder[]>([]);
  const [pendingSource, setPendingSource] = React.useState("");
  const [cancelingOrdId, setCancelingOrdId] = React.useState("");
  const [closingWorkbenchKey, setClosingWorkbenchKey] = React.useState("");
  const [ordersWarning, setOrdersWarning] = React.useState("");
  const pendingRequestSeqRef = React.useRef(0);

  React.useEffect(() => {
    const normalized = initialInstId.trim().toUpperCase();
    if (normalized.endsWith("-SWAP") && normalized !== instId.toUpperCase()) {
      setInstId(normalized);
    }
  }, [initialInstId, instId]);

  const activeEnvironment = settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  const tradeEnabled = Boolean(settings?.tradeEnabled);
  const selectedInstrument = React.useMemo(
    () => instruments.find((item) => item.inst_id === instId.toUpperCase()),
    [instruments, instId]
  );
  const latestTicker = tickers[instId.toUpperCase()];
  const marginCurrency = marginCurrencyForInstrument(selectedInstrument, instId);
  const marginAvailable = React.useMemo(
    () => availableBalanceForCurrency(tradingAccount, marginCurrency),
    [marginCurrency, tradingAccount]
  );
  const marginBlockMessage = React.useMemo(() => {
    if (!tradeEnabled || !tradingAccount?.configured || !tradingAccount.summary || !marginCurrency) return "";
    if (marginAvailable === null) {
      return `当前${environmentLabel(activeEnvironment)}账户没有 ${marginCurrency} 可用保证金，${instId.toUpperCase()} 会被 OKX 拒单。请换用有保证金的合约，或在 OKX ${environmentLabel(activeEnvironment)}补充 ${marginCurrency}。`;
    }
    if (marginAvailable <= 0) {
      return `当前${environmentLabel(activeEnvironment)}账户 ${marginCurrency} 可用保证金为 0，${instId.toUpperCase()} 会被 OKX 拒单。`;
    }
    return "";
  }, [activeEnvironment, instId, marginAvailable, marginCurrency, tradeEnabled, tradingAccount]);
  const marginNotice = React.useMemo(() => {
    if (!tradingAccount?.configured || !tradingAccount.summary || !marginCurrency) return "";
    if (marginBlockMessage) return marginBlockMessage;
    return `保证金币种 ${marginCurrency} · 可用 ${formatOrderNumber(marginAvailable, 8)} ${marginCurrency}`;
  }, [marginAvailable, marginBlockMessage, marginCurrency, tradingAccount]);
  const localPaperAvailable = activeEnvironment === "simulated" && Boolean(marginBlockMessage);
  const currentLeverage = React.useMemo(() => leverageForPosition(leverageRows, posSide), [leverageRows, posSide]);
  const leverageValue = React.useMemo(() => parseLeverageInput(leverageInput), [leverageInput]);
  const leverageValid = leverageValue !== null && leverageValue > 0;
  const leverageChanged =
    leverageValid && (currentLeverage === null || Math.abs(leverageValue - currentLeverage) > 0.000001);
  const leverageScope = leverageScopeLabel(tdMode, posSide);
  const leverageSummary = leverageRowsSummary(leverageRows);
  const priceRequired = orderNeedsPrice(ordType);
  const quantityLabel = quantityUnitLabel(quantityUnit, instId);
  const quantityPrice = priceRequired ? toNumber(px) ?? toNumber(latestTicker?.last) : toNumber(latestTicker?.last);
  const submitQuantityPrice = priceRequired ? toNumber(px) : toNumber(latestTicker?.last);
  const minOrderSize = minimumQuantityForUnit(quantityUnit, selectedInstrument, instId, quantityPrice);
  const quantityEstimate = React.useMemo(
    () => (sz.trim() ? contractsFromQuantity(sz, quantityUnit, selectedInstrument, instId, quantityPrice) : null),
    [instId, quantityPrice, quantityUnit, selectedInstrument, sz]
  );
  const quantityUnitOptions = React.useMemo(() => {
    const { base, quote } = instrumentCurrencies(instId);
    return [
      { key: "contracts", label: "张" },
      { key: "base", label: base },
      { key: "quote", label: quote }
    ];
  }, [instId]);
  const matchingInstruments = React.useMemo(() => {
    const keyword = contractSearch.trim().toUpperCase();
    return instruments
      .filter((item) => instrumentMatchesFilter(item, contractFilter))
      .filter((item) => instrumentMatchesKeyword(item, keyword))
      .sort((left, right) => {
        return compareInstrumentRelevance(left, right, {
          selectedInstId: instId,
          sortMode: "default",
          tickers
        });
      })
      .slice(0, MAX_TRADE_INSTRUMENT_OPTIONS);
  }, [contractFilter, contractSearch, instruments, instId, tickers]);
  const contractFilterTotal = React.useMemo(
    () => instruments.filter((item) => instrumentMatchesFilter(item, contractFilter)).length,
    [contractFilter, instruments]
  );
  const advancedOrderTypeSelected = advancedOrderTypeOptions.some((item) => item.key === ordType);
  const visibleAdvancedOrderTypes = showAdvancedOrderTypes || advancedOrderTypeSelected;
  const leverageDisplay = leverageLoading ? "读取中" : formatLeverage(currentLeverage);
  const leverageContext = `${instId.toUpperCase()} · ${leverageScope}`;

  // 工作台概览数据：复用 /api/account 已返回的 positions 与 summary
  const workbenchPositions = React.useMemo(
    () => (tradingAccount?.positions ?? []).filter(positionIsOpen),
    [tradingAccount]
  );
  const workbenchDetails = React.useMemo(
    () => (tradingAccount?.summary ? accountDetails(tradingAccount.summary) : []),
    [tradingAccount]
  );
  const workbenchTotalEquity = React.useMemo(
    () => (tradingAccount?.summary ? firstMetric(tradingAccount.summary, workbenchDetails, "totalEq", ["eqUsd"]) : ""),
    [tradingAccount, workbenchDetails]
  );
  const workbenchUpl = React.useMemo(
    () => workbenchPositions.reduce((sum, item) => sum + (positionNumber(item, ["upl"]) ?? 0), 0),
    [workbenchPositions]
  );

  const loadSettings = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/settings/status`);
    if (!response.ok) throw new Error("设置加载失败");
    setSettings(await response.json());
  }, []);

  const loadTradingAccount = React.useCallback(async (force = false, skipThrottle = false) => {
    if (accountLoadingRef.current) return;
    // 节流：REST 轮询与 WS 私有频道事件都会触发刷新。后端 /api/account 自带缓存，
    // 短窗口内的 force 拉取无新数据，跳过可避免 WS 事件风暴放大账户接口调用。
    // 下单/切环境等关键操作传 skipThrottle=true，保证状态立即刷新，不受节流影响。
    const now = Date.now();
    if (force && !skipThrottle && now - accountLastFetchRef.current < ACCOUNT_REFRESH_MIN_MS) return;
    accountLastFetchRef.current = now;
    // seq 防竞态：只让最后一次请求的结果落盘，避免旧的慢响应覆盖新快照。
    const requestSeq = accountRequestSeqRef.current + 1;
    accountRequestSeqRef.current = requestSeq;
    accountLoadingRef.current = true;
    try {
      const response = await fetch(`${API_BASE}/api/account${force ? "?force=true" : ""}`);
      if (!response.ok) return;
      const payload = await response.json();
      if (requestSeq === accountRequestSeqRef.current) setTradingAccount(payload);
    } finally {
      accountLoadingRef.current = false;
    }
  }, []);

  const loadLeverage = React.useCallback(async () => {
    const normalizedInstId = instId.trim().toUpperCase();
    if (!normalizedInstId.endsWith("-SWAP")) return;
    const requestSeq = leverageRequestSeqRef.current + 1;
    leverageRequestSeqRef.current = requestSeq;
    leverageLoadingRef.current = true;
    setLeverageLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/trading/leverage?instId=${encodeURIComponent(normalizedInstId)}&tdMode=${encodeURIComponent(tdMode)}`
      );
      if (!response.ok) {
        if (requestSeq === leverageRequestSeqRef.current) setLeverageRows([]);
        return;
      }
      const payload: LeverageResponse = await response.json();
      if (requestSeq === leverageRequestSeqRef.current) setLeverageRows(payload.data ?? []);
    } finally {
      if (requestSeq === leverageRequestSeqRef.current) {
        leverageLoadingRef.current = false;
        setLeverageLoading(false);
      }
    }
  }, [instId, tdMode]);

  const switchEnvironment = async (environment: "simulated" | "live") => {
    if (environment === activeEnvironment) return;
    if (
      environment === "live" &&
      !(await confirmAction("确认切换到真实盘？默认只读；只有后端开启实盘交易授权时才可下单。"))
    ) {
      return;
    }
    setSubmitting(true);
    setWarning("");
    try {
      const response = await fetch(`${API_BASE}/api/settings/trading-environment`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ environment })
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "交易环境切换失败");
      }
      setSettings(await response.json());
      await loadTradingAccount(true, true);
      await loadLeverage();
      setStatus(`${environmentLabel(environment)}已切换`);
    } catch (error) {
      setWarning(error instanceof Error ? error.message : "交易环境切换失败");
    } finally {
      setSubmitting(false);
    }
  };

  // 工作台就地撤单：复用订单页的确认+环境隔离语义，成功后同步刷新挂单与账户。
  const cancelWorkbenchOrder = async (order: PendingOrder) => {
    const ordId = (order.ordId ?? "").trim();
    const clOrdId = (order.clOrdId ?? "").trim();
    const orderKey = ordId || clOrdId || `${order.instId ?? ""}-${order.ctime ?? ""}`;
    const detail = [
      `环境：${environmentLabel(activeEnvironment)}`,
      `合约：${order.instId ?? "--"}`,
      `方向：${orderTradeDirectionLabel(order.side?.toLowerCase() ?? "", false)}`,
      `订单号：${orderKey}`
    ].join("\n");
    if (!(await confirmAction(`确认撤销以下挂单？\n${detail}`))) return;
    setCancelingOrdId(orderKey);
    setOrdersWarning("");
    try {
      const response = await fetch(`${API_BASE}/api/trading/orders/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          environment: activeEnvironment,
          instId: order.instId,
          ordId: ordId || undefined,
          clOrdId: ordId ? undefined : clOrdId
        })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "撤销挂单失败");
      setStatus("挂单已撤销");
      await Promise.all([loadPendingOrders(), loadTradingAccount(true, true)]);
    } catch (error) {
      setOrdersWarning(error instanceof Error ? error.message : "撤销挂单失败");
    } finally {
      setCancelingOrdId("");
    }
  };

  // 工作台快速平仓：市价全平，确认后走后端 reduceOnly 平仓端点。
  const quickClosePosition = async (position: Record<string, string>) => {
    if (!tradeEnabled) {
      setOrdersWarning(tradeBlockedDetail(settings));
      return;
    }
    const closeOrder = positionCloseOrder(position);
    if (!closeOrder) {
      setOrdersWarning("该持仓没有可平数量。");
      return;
    }
    const rowKey = `${closeOrder.instId}-${closeOrder.posSide}`;
    const confirmLines = [
      `环境：${environmentLabel(activeEnvironment)}`,
      `合约：${closeOrder.instId}`,
      `方向：${closeOrder.label}`,
      `可平：${closeOrder.sz} 张`,
      "方式：市价全平"
    ];
    const liveWarning = activeEnvironment === "live" ? "\n\n注意：这会向 OKX 真实盘提交平仓请求。" : "";
    if (!(await confirmAction(`确认提交市价平仓？\n${confirmLines.join("\n")}${liveWarning}`))) return;
    setClosingWorkbenchKey(rowKey);
    setOrdersWarning("");
    try {
      const response = await fetch(`${API_BASE}/api/trading/positions/close`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instId: closeOrder.instId,
          mgnMode: positionCloseTradeMode(position),
          posSide: closeOrder.posSide,
          autoCxl: false,
          environment: activeEnvironment
        })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "平仓提交失败");
      setStatus("市价平仓请求已提交");
      await Promise.all([loadTradingAccount(true, true), loadPendingOrders()]);
    } catch (error) {
      setOrdersWarning(error instanceof Error ? error.message : "平仓提交失败");
    } finally {
      setClosingWorkbenchKey("");
    }
  };

  const loadInstruments = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/instruments?limit=2000`);
    if (!response.ok) throw new Error("合约加载失败");
    const payload = await response.json();
    setInstruments(payload.data ?? []);
  }, []);

  const loadTickers = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/tickers`);
    if (!response.ok) return;
    const payload = await response.json();
    const rows: Ticker[] = payload.data ?? [];
    if (payload.warning && rows.length === 0) {
      setWarning(payload.warning);
    }
    setTickers(
      rows.reduce<Record<string, Ticker>>((next, item) => {
        if (item.instId) next[item.instId] = item;
        return next;
      }, {})
    );
  }, []);

  // 工作台挂单：与订单页同源（/api/trading/orders 的 pending），只取可撤销的挂单。
  // seq 防竞态，避免慢响应覆盖最新挂单视图。
  const loadPendingOrders = React.useCallback(async () => {
    const requestSeq = pendingRequestSeqRef.current + 1;
    pendingRequestSeqRef.current = requestSeq;
    try {
      const response = await fetch(`${API_BASE}/api/trading/orders?limit=100`);
      if (!response.ok) return;
      const payload: SimOrdersResponse = await response.json();
      if (requestSeq !== pendingRequestSeqRef.current) return;
      setPendingOrders(
        (payload.pending ?? []).filter(
          (order) => order.state === "live" || order.state === "partially_filled"
        )
      );
      setPendingSource(payload.source ?? "");
    } catch {
      // 挂单是辅助视图，读取失败时保留上次数据，不打扰下单主流程
    }
  }, []);


  React.useEffect(() => {
    loadSettings().catch((error) => setWarning(error.message));
    loadTradingAccount().catch(() => undefined);
    loadLeverage().catch(() => undefined);
    loadInstruments().catch((error) => setWarning(error.message));
    loadTickers().catch(() => undefined);
    loadPendingOrders().catch(() => undefined);
  }, [loadInstruments, loadLeverage, loadPendingOrders, loadSettings, loadTickers, loadTradingAccount]);

  React.useEffect(() => {
    loadLeverage().catch(() => undefined);
  }, [activeEnvironment, loadLeverage]);

  React.useEffect(() => {
    setLeverageDirty(false);
  }, [instId, tdMode, posSide]);

  React.useEffect(() => {
    if (!leverageDirty) {
      setLeverageInput(currentLeverage !== null ? formatOrderNumber(currentLeverage, 2) : "");
    }
  }, [currentLeverage, leverageDirty]);

  React.useEffect(() => {
    const refreshVisibleTrade = () => {
      if (!document.hidden) {
        loadTickers().catch(() => undefined);
        loadTradingAccount().catch(() => undefined);
        loadLeverage().catch(() => undefined);
        loadPendingOrders().catch(() => undefined);
        setUpdatedAt(Date.now());
      }
    };
    const timer = window.setInterval(refreshVisibleTrade, ORDER_POLL_MS);
    document.addEventListener("visibilitychange", refreshVisibleTrade);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshVisibleTrade);
    };
  }, [loadLeverage, loadPendingOrders, loadTickers, loadTradingAccount]);

  const tradeRealtime = useRealtimeFeed({
    topics: ["market.ticker", "account", "positions"],
    instId: instId.toUpperCase(),
    instIds: [instId.toUpperCase()],
    environment: activeEnvironment,
    onSnapshotRequired: (payload) => {
      if (payload.topic === "market.ticker") loadTickers().catch(() => undefined);
      if (payload.topic === "account" || payload.topic === "positions") loadTradingAccount(true).catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "market.ticker" && payload.instId && payload.data) {
        setTickers((current) => ({ ...current, [payload.instId as string]: payload.data as Ticker }));
        setStatus("实时价格已更新");
      }
      if (payload.type === "account.update" || payload.type === "position.update") {
        // 刷新由上面的 onSnapshotRequired（refreshRequired）统一驱动，这里只更新提示，
        // 避免同一事件触发两次账户拉取。若后端事件未带 refreshRequired，则由 REST 轮询兜底。
        setStatus(payload.type === "account.update" ? "账户信息有实时更新" : "持仓信息有实时更新");
      }
      if (payload.type === "disabled" && ["account", "positions"].includes(payload.topic ?? "")) {
        setStatus(payload.message ?? "私有实时频道未启用");
      }
      if (payload.type === "error" || payload.type === "stale") {
        setWarning(payload.message ?? payload.warning ?? "实时通道暂不可用，已保留 REST 回退");
      }
    }
  });

  React.useEffect(() => {
    if (!instrumentPickerOpen) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (event.target instanceof Node && !instrumentPickerRef.current?.contains(event.target)) {
        setInstrumentPickerOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setInstrumentPickerOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [instrumentPickerOpen]);

  const selectTradeInstrument = (instrument: Instrument) => {
    leverageRequestSeqRef.current += 1;
    setInstId(instrument.inst_id);
    setContractSearch("");
    setInstrumentPickerOpen(false);
    setPx("");
    setSz("");
    setLeverageRows([]);
    setLeverageInput("");
    setLeverageDirty(false);
    setLeverageLoading(false);
    setWarning("");
  };

  React.useEffect(() => {
    if (!sz.trim() && minOrderSize && minOrderSize !== "--") {
      setSz(minOrderSize);
    }
  }, [minOrderSize, sz]);

  const changeQuantityUnit = (value: string) => {
    setQuantityUnit(value as QuantityUnit);
    setSz("");
    setWarning("");
  };

  const changeTradeMode = (value: string) => {
    leverageRequestSeqRef.current += 1;
    setTdMode(value);
    setLeverageRows([]);
    setLeverageInput("");
    setLeverageDirty(false);
    setLeverageLoading(false);
    setWarning("");
  };

  const changeTradeSide = (value: string) => {
    setSide(value);
    setLeverageDirty(false);
    setWarning("");
  };

  const changeReduceOnly = (value: boolean) => {
    setReduceOnly(value);
    setLeverageDirty(false);
    setWarning("");
  };

  const quantityPreview = React.useMemo(() => {
    if (!quantityEstimate) return "";
    if ("error" in quantityEstimate) return quantityEstimate.error ?? "";
    const parts = [`实际提交 ${quantityEstimate.contractsText} 张`];
    if (quantityEstimate.baseAmount) {
      parts.push(`约 ${formatOrderNumber(quantityEstimate.baseAmount, 8)} ${quantityEstimate.base}`);
    }
    if (quantityEstimate.quoteAmount) {
      parts.push(`名义约 ${formatOrderNumber(quantityEstimate.quoteAmount, 4)} ${quantityEstimate.quote}`);
    }
    const marginEstimate = estimatedMarginForContracts(quantityEstimate, marginCurrency, currentLeverage);
    if (marginEstimate) {
      parts.push(
        `预估保证金约 ${formatOrderNumber(marginEstimate.amount, 8)} ${marginEstimate.currency} (${formatOrderNumber(currentLeverage, 2)}x)`
      );
    }
    return parts.join(" · ");
  }, [currentLeverage, marginCurrency, quantityEstimate]);
  const quantityPreviewError = Boolean(quantityEstimate && "error" in quantityEstimate);

  const applyLeverage = async () => {
    setWarning("");
    const normalizedInstId = instId.trim().toUpperCase();
    if (!tradeEnabled) {
      setWarning(`${environmentLabel(activeEnvironment)}交易设置未开启。`);
      return;
    }
    if (!normalizedInstId.endsWith("-SWAP")) {
      setWarning("请选择 OKX 永续合约。");
      return;
    }
    if (!leverageValid || leverageValue === null) {
      setWarning("请输入有效的杠杆倍数。");
      return;
    }

    const lever = formatOrderNumber(leverageValue, 4);
    if (
      activeEnvironment === "live" &&
      !(await confirmAction(`确认修改真实盘 ${normalizedInstId} ${leverageScope}杠杆为 ${lever}x？`))
    ) {
      return;
    }

    setApplyingLeverage(true);
    try {
      const response = await fetch(`${API_BASE}/api/trading/leverage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instId: normalizedInstId,
          mgnMode: tdMode,
          posSide,
          lever,
          environment: activeEnvironment
        })
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "杠杆设置失败");
      }
      const payload: LeverageUpdateResponse = await response.json();
      const fallbackRow: LeverageInfo = {
        instId: normalizedInstId,
        mgnMode: tdMode,
        posSide: tdMode === "isolated" ? posSide : "net",
        lever
      };
      setLeverageRows(payload.data?.length ? payload.data : [fallbackRow]);
      setLeverageInput(lever);
      setLeverageDirty(false);
      setStatus(`${environmentLabel(activeEnvironment)}${leverageScope}杠杆已设置为 ${lever}x`);
      await loadLeverage();
      await loadTradingAccount(true, true);
    } catch (error) {
      setWarning(error instanceof Error ? error.message : "杠杆设置失败");
    } finally {
      setApplyingLeverage(false);
    }
  };

  const submitOrder = async (event?: React.FormEvent, localOnly = false) => {
    event?.preventDefault();
    if (submitting) return;
    setWarning("");
    if (!localOnly && !tradeEnabled) {
      setWarning(`${environmentLabel(activeEnvironment)}下单未开启。`);
      return;
    }
    if (localOnly && activeEnvironment !== "simulated") {
      setWarning("本地模拟订单只能在虚拟盘环境提交。");
      return;
    }
    if (!instId.trim().toUpperCase().endsWith("-SWAP")) {
      setWarning("请选择 OKX 永续合约。");
      return;
    }
    if (!sz.trim()) {
      setWarning("请填写下单数量。");
      return;
    }
    if (priceRequired && !px.trim()) {
      setWarning("请填写委托价格。");
      return;
    }
    if (!localOnly && marginBlockMessage) {
      setWarning(marginBlockMessage);
      return;
    }

    const normalizedInstId = instId.trim().toUpperCase();
    const submitEstimate = contractsFromQuantity(sz, quantityUnit, selectedInstrument, normalizedInstId, submitQuantityPrice);
    if ("error" in submitEstimate) {
      setWarning(submitEstimate.error ?? "下单数量换算失败。");
      return;
    }
    const submitSize = submitEstimate.contractsText;
    const summary = [
      `合约：${normalizedInstId}`,
      `交易方向：${orderTradeDirectionLabel(side, reduceOnly)}`,
      `类型：${orderTypeLabel(ordType)}`,
      `价格：${priceRequired ? px.trim() : "市价"}`,
      `输入数量：${sz.trim()} ${quantityLabel}`,
      `提交张数：${submitSize} 张`
    ].join("\n");
    const targetLabel = localOnly ? "本地模拟" : `OKX ${environmentLabel(activeEnvironment)}`;
    const confirmExtra = localOnly ? "\n\n本地模拟订单只保存到数据库，不会发送到 OKX。" : "";
    if (!(await confirmAction(`确认提交 ${targetLabel}订单？\n${summary}${confirmExtra}`))) return;

    if (!pendingClOrdIdRef.current) pendingClOrdIdRef.current = makeClientOrderId();
    const clOrdId = pendingClOrdIdRef.current;
    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/trading/orders${localOnly ? "/local" : ""}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instId: normalizedInstId,
          tdMode,
          side,
          posSide,
          ordType,
          sz: submitSize,
          px: priceRequired ? px.trim() : undefined,
          reduceOnly,
          environment: activeEnvironment,
          clOrdId
        })
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "订单提交失败");
      }
      await response.json().catch(() => ({}));
      setStatus(
        localOnly
          ? "本地模拟订单已保存，可在「订单」页查看"
          : `${environmentLabel(activeEnvironment)}订单已提交，可在「订单」页查看`
      );
      setUpdatedAt(Date.now());
      // 提交成功后清空幂等键：下一次提交是新的意图，生成新的 clOrdId。
      pendingClOrdIdRef.current = "";
    } catch (error) {
      // 失败保留 clOrdId（含网络错误），同一意图重试复用，避免 OKX 重复成交。
      setWarning(error instanceof Error ? error.message : "订单提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="tradePage tradePageWorkbench">
      <PageHeader eyebrow="手动交易" title="OKX 交易环境" description={`${status}${updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={
        <div className="workspaceActions">
          <div className="environmentSwitch" aria-label="交易环境切换">
            <Button type="button" variant="subtle"
              className={activeEnvironment === "simulated" ? "selected" : ""}
              onClick={() => switchEnvironment("simulated")}
              disabled={submitting || applyingLeverage}
            >
              虚拟盘
            </Button>
            <Button type="button" variant="subtle"
              className={activeEnvironment === "live" ? "selected danger" : ""}
              onClick={() => switchEnvironment("live")}
              disabled={submitting || applyingLeverage}
            >
              真实盘
            </Button>
          </div>
          <div className="statusPills" aria-label="交易状态">
            <Badge className={`statusPill ${tradeRealtime.connected ? "live" : "warning"}`}>
              {tradeRealtime.connected ? "实时通道" : "REST 回退"}
            </Badge>
            <Badge className={`statusPill ${tradeEnabled ? "live" : "warning"}`}>
              {tradeStatusLabel(settings)}
            </Badge>
            <Badge className={`statusPill ${settings?.demoHasCredentials ? "live" : "warning"}`}>
              {apiCredentialLabel("虚拟盘", settings?.demoHasCredentials)}
            </Badge>
            <Badge className={`statusPill ${settings?.liveHasCredentials ? "live" : "warning"}`}>
              {apiCredentialLabel("真实盘", settings?.liveHasCredentials)}
            </Badge>
          </div>
          {onOpenOrders ? (
            <Button type="button" variant="default" className="secondaryButton" onClick={onOpenOrders} leftSection={<Receipt size={16} />}>
              订单记录
            </Button>
          ) : null}
          <IconButton
            label="刷新账户与行情"
            onClick={() => {
              loadSettings().catch(() => undefined);
              loadInstruments().catch(() => undefined);
              loadTickers().catch(() => undefined);
              loadLeverage().catch(() => undefined);
              setUpdatedAt(Date.now());
            }}
          >
            <RefreshCw size={16} />
          </IconButton>
        </div>
      } />
      {warning ? <Notice tone="danger">{warning}</Notice> : null}

      <section className="tradeWorkbenchOverview" aria-label="交易概览">
        <div className="workbenchOverviewHead">
          <div className="workbenchOverviewTitle">
            <WalletCards size={17} aria-hidden="true" />
            <strong>账户概览</strong>
            <span className={`stateBadge ${tradingAccount?.configured ? "live" : ""}`}>
              {tradingAccount?.configured ? environmentLabel(activeEnvironment) : "账户未连接"}
            </span>
          </div>
          <div className="workbenchOverviewMetrics">
            <MiniMetric label="账户权益" value={formatValue(workbenchTotalEquity)} />
            <MiniMetric label={`可用保证金 · ${marginCurrency || "--"}`} value={formatOrderNumber(marginAvailable)} />
            <MiniMetric
              label="未实现盈亏"
              value={formatSignedValue(workbenchUpl)}
              valueClass={pnlValueClass(workbenchUpl)}
            />
            <MiniMetric label="当前持仓" value={`${workbenchPositions.length} 个`} />
            <MiniMetric label="当前挂单" value={`${pendingOrders.length} 笔`} />
          </div>
        </div>
      </section>

      {ordersWarning ? <Notice tone="danger">{ordersWarning}</Notice> : null}

      <section className="tradeGrid tradeGridWorkbench">
        <form className="tradeTicket" onSubmit={submitOrder}>
          <PanelHeader
            icon={<Send size={17} />}
            title="下单面板"
            meta={tradeEnabled ? `${environmentLabel(activeEnvironment)}可下单` : tradeBlockedTitle(settings)}
          />

          <div className="fieldBlock">
            <span>合约</span>
            <div className={`contractPicker ${instrumentPickerOpen ? "open" : ""}`} ref={instrumentPickerRef}>
              <UnstyledButton
                className="contractPickerButton"
                type="button"
                aria-haspopup="listbox"
                aria-expanded={instrumentPickerOpen}
                onClick={() => {
                  const nextOpen = !instrumentPickerOpen;
                  setInstrumentPickerOpen(nextOpen);
                  if (nextOpen) setContractSearch("");
                }}
              >
                <span className="contractPickerMain">
                  <strong>{instId.toUpperCase()}</strong>
                  <small>
                    {selectedInstrument ? instrumentSummaryLabel(selectedInstrument, instId) : "等待合约列表"}
                  </small>
                </span>
                <span className={`stateBadge ${selectedInstrument?.state === "live" ? "live" : ""}`}>
                  {stateLabel(selectedInstrument?.state)}
                </span>
                <ChevronDown size={16} aria-hidden="true" />
              </UnstyledButton>

              {instrumentPickerOpen ? (
                <div className="contractPickerPanel">
                  <TextInput
                    className="contractPickerSearch"
                    leftSection={<Search size={15} aria-hidden="true" />}
                    autoFocus
                    value={contractSearch}
                    onChange={(event) => setContractSearch(event.target.value.toUpperCase())}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        if (matchingInstruments[0]) selectTradeInstrument(matchingInstruments[0]);
                      }
                    }}
                    placeholder="搜索 BTC / ETH / USDT"
                    aria-label="搜索可交易合约"
                  />

                  <div className="contractPickerFilters" aria-label="交易合约筛选">
                    {tradeInstrumentFilters.map((item) => (
                      <UnstyledButton
                        key={item.key}
                        type="button"
                        className={contractFilter === item.key ? "selected" : ""}
                        onClick={() => setContractFilter(item.key)}
                      >
                        {item.label}
                      </UnstyledButton>
                    ))}
                  </div>

                  <div className="contractPickerSummary">
                    <span>{matchingInstruments.length} 个结果</span>
                    <span>{contractFilterTotal}/{instruments.length || 0}</span>
                  </div>

                  <div className="contractPickerList" role="listbox" aria-label="可选择合约">
                    {matchingInstruments.length === 0 ? (
                      <EmptyState compact>没有符合条件的合约</EmptyState>
                    ) : (
                      matchingInstruments.map((item) => {
                        const itemTicker = tickers[item.inst_id];
                        const itemChange = tickerTodayChange(itemTicker);
                        const selectedOption = instId.toUpperCase() === item.inst_id;
                        return (
                          <UnstyledButton
                            key={item.inst_id}
                            className={`contractOption ${selectedOption ? "selected" : ""}`}
                            type="button"
                            role="option"
                            aria-selected={selectedOption}
                            onClick={() => selectTradeInstrument(item)}
                            title={`${instrumentSummaryLabel(item, item.inst_id)} · 最小下单 ${item.lot_sz ?? "--"}`}
                          >
                            <span className="contractOptionMain">
                              <strong>{item.inst_id}</strong>
                              <small>{instrumentSummaryLabel(item, item.inst_id)}</small>
                            </span>
                            <span className="contractOptionMarket">
                              <strong>{formatMarketNumber(itemTicker?.last)}</strong>
                              <small
                                className={changeClass(itemChange.percent)}
                                title="今日涨跌（按 UTC+8 日开盘价计算）"
                                aria-label={`今日涨跌 ${formatSignedPercent(itemChange.percent)}`}
                              >
                                {formatSignedPercent(itemChange.percent)}
                              </small>
                            </span>
                            <span className={`stateBadge ${item.state === "live" ? "live" : ""}`}>{stateLabel(item.state)}</span>
                            <span className="contractOptionCheck">{selectedOption ? <Check size={15} /> : null}</span>
                          </UnstyledButton>
                        );
                      })
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          <section className="tradeTicketSection tradeMarketCard" aria-label="当前合约概览">
            <div className="tradeFacts">
              <span>最新价 <strong>{formatMarketNumber(latestTicker?.last)}</strong></span>
              <span>面值 <strong>{contractValueLabel(selectedInstrument, instId)}</strong></span>
              <span>最小变动 <strong>{selectedInstrument?.tick_sz ?? "--"}</strong></span>
              <span>最小下单 <strong>{selectedInstrument?.lot_sz ?? "--"}</strong></span>
            </div>
          </section>

          <section className="tradeTicketSection leverageSection" aria-label="当前合约杠杆">
            <SegmentedField label="保证金模式" value={tdMode} options={tradeModeOptions} onChange={changeTradeMode} />
            <div className="leverageControl">
              <div className="leverageMeta">
                <span>
                  <strong>{leverageContext}</strong>
                  <small>账户当前 {leverageLoading ? "读取中" : leverageSummary}</small>
                </span>
                <em className={leverageDirty && leverageChanged ? "dirty" : ""}>
                  {leverageDirty && leverageChanged ? "未应用" : leverageDisplay}
                </em>
              </div>
              <div className="leveragePresets" aria-label="选择杠杆倍数">
                {leveragePresetOptions.map((item) => (
                  <Button variant="default" size="xs"
                    key={item}
                    type="button"
                    className={leverageValue !== null && Math.abs(leverageValue - item) < 0.000001 ? "selected" : ""}
                    onClick={() => {
                      setLeverageInput(String(item));
                      setLeverageDirty(true);
                      setWarning("");
                    }}
                  >
                    {item}x
                  </Button>
                ))}
              </div>
              <div className="fieldWithAction leverageInput">
                <TextInput
                  value={leverageInput}
                  inputMode="decimal"
                  onChange={(event) => {
                    setLeverageInput(event.target.value);
                    setLeverageDirty(true);
                    setWarning("");
                  }}
                  placeholder="杠杆倍数"
                  aria-label="杠杆倍数"
                />
                <Button variant="default" size="xs"
                  type="button"
                  onClick={applyLeverage}
                  disabled={!tradeEnabled || applyingLeverage || !leverageValid || !leverageChanged}
                  title={!tradeEnabled ? tradeBlockedDetail(settings) : undefined}
                >
                  <Check size={14} aria-hidden="true" />
                  {applyingLeverage ? "应用中" : "应用"}
                </Button>
              </div>
            </div>
          </section>

          <section className="tradeTicketSection tradeOrderConfig" aria-label="订单参数">
            <SegmentedField label="交易方向" value={side} options={tradeDirectionOptions} onChange={changeTradeSide} tone={side} />
            <SegmentedField
              label="常用类型"
              value={ordType}
              options={primaryOrderTypeOptions}
              onChange={(value) => {
                setOrdType(value);
                setShowAdvancedOrderTypes(false);
              }}
            />
            <div className="advancedOrderType">
              <Button
                type="button"
                variant="subtle"
                size="xs"
                className="inlineToggleButton"
                aria-expanded={visibleAdvancedOrderTypes}
                onClick={() => setShowAdvancedOrderTypes((value) => !value)}
              >
                <ListChecks size={14} aria-hidden="true" />
                {advancedOrderTypeSelected ? "高级类型已选" : visibleAdvancedOrderTypes ? "收起更多选项" : "更多选项"}
              </Button>
              {visibleAdvancedOrderTypes ? (
                <>
                  <SegmentedField label="数量单位" value={quantityUnit} options={quantityUnitOptions} onChange={changeQuantityUnit} />
                  <SegmentedField label="高级类型" value={ordType} options={advancedOrderTypeOptions} onChange={setOrdType} />
                </>
              ) : null}
            </div>
          </section>

          <section className="tradeTicketSection tradeSubmitSection" aria-label="提交参数">
            <div className="fieldGrid">
              <label className="fieldBlock">
                <span>委托价格</span>
                <div className="fieldWithAction">
                  <TextInput
                    value={priceRequired ? px : ""}
                    disabled={!priceRequired}
                    inputMode="decimal"
                    onChange={(event) => setPx(event.target.value)}
                    placeholder={priceRequired ? "价格" : "市价不填"}
                  />
                  <Button variant="default" size="xs"
                    type="button"
                    onClick={() => latestTicker?.last && setPx(latestTicker.last)}
                    disabled={!priceRequired || !latestTicker?.last}
                  >
                    最新价
                  </Button>
                </div>
              </label>
              <label className="fieldBlock">
                <span>数量（{quantityLabel}）</span>
                <TextInput
                  value={sz}
                  inputMode="decimal"
                  onChange={(event) => setSz(event.target.value)}
                  placeholder={`最小 ${minOrderSize || "--"} ${quantityLabel}`}
                />
              </label>
            </div>

            <div className="tradePreviewStack">
              {quantityPreview ? (
                <div className={`quantityPreview ${quantityPreviewError ? "error" : ""}`}>{quantityPreview}</div>
              ) : null}

              {marginNotice ? (
                <div className={`quantityPreview ${marginBlockMessage ? "error" : ""}`}>{marginNotice}</div>
              ) : null}
            </div>

            <Checkbox className="checkField" label="只减仓" checked={reduceOnly} onChange={(event) => changeReduceOnly(event.target.checked)} />

            {!tradeEnabled ? (
              <div className="tradeLockPanel">
                <ShieldCheck size={17} aria-hidden="true" />
                <div>
                  <strong>{tradeBlockedTitle(settings)}</strong>
                  <span>{tradeBlockedDetail(settings)}</span>
                </div>
                {activeEnvironment === "live" && settings?.demoHasCredentials ? (
                  <Button type="button" variant="subtle" size="xs" onClick={() => switchEnvironment("simulated")} disabled={submitting || applyingLeverage}>
                    切回虚拟盘
                  </Button>
                ) : null}
              </div>
            ) : null}

            <Button
              className="primaryButton"
              type="submit"
              disabled={!tradeEnabled || submitting || applyingLeverage || Boolean(marginBlockMessage)}
              title={!tradeEnabled ? tradeBlockedDetail(settings) : marginBlockMessage || undefined}
            >
              <Send size={16} aria-hidden="true" />
              {submitting ? "提交中" : `提交${environmentLabel(activeEnvironment)}订单`}
            </Button>

            {localPaperAvailable ? (
              <Button variant="default"
                className="secondaryButton"
                type="button"
                onClick={() => submitOrder(undefined, true)}
                disabled={submitting || applyingLeverage}
                title="只保存到本地数据库，不发送到 OKX"
              >
                <Database size={16} />
                保存本地模拟订单
              </Button>
            ) : null}
          </section>
        </form>

        <div className="tradeWorkbenchSide">
          <section className="workbenchPanel workbenchPositionsPanel" aria-label="当前持仓">
            <PanelHeader
              icon={<WalletCards size={17} />}
              title="当前持仓"
              meta={`${workbenchPositions.length} 个 · ${environmentLabel(activeEnvironment)}`}
            />
            {!tradingAccount?.configured ? (
              <EmptyState compact>{tradingAccount?.message ?? "账户未连接，暂无持仓"}</EmptyState>
            ) : workbenchPositions.length === 0 ? (
              <EmptyState compact>当前{environmentLabel(activeEnvironment)}没有持仓</EmptyState>
            ) : (
              <div className="workbenchTableWrap">
                <DataTable className="minimalDataTable workbenchPositionTable">
                  <thead>
                    <tr><th>合约</th><th>方向</th><th>持仓 / 可平</th><th>均价 / 标记</th><th>未实现盈亏</th><th>操作</th></tr>
                  </thead>
                  <tbody>
                    {workbenchPositions.map((item, index) => {
                      const upl = positionNumber(item, ["upl"]);
                      const ratio = positionNumber(item, ["uplRatio"]);
                      const direction = normalizedPositionSide(item.posSide);
                      const closeOrder = positionCloseOrder(item);
                      const rowKey = `${closeOrder?.instId ?? item.instId}-${closeOrder?.posSide ?? direction}`;
                      const isClosing = closingWorkbenchKey === rowKey;
                      return (
                        <tr key={`${item.instId}-${item.posSide}-${item.posId}-${index}`} title={`更新时间 ${formatTime(positionText(item, ["uTime", "cTime"], ""))}`}>
                          <td>
                            <strong>{positionText(item, ["instId"])}</strong>
                            <small>{positionText(item, ["ccy"])} 保证金</small>
                          </td>
                          <td>
                            <Badge className={`signalLogActionTag ${direction === "long" ? "up" : direction === "short" ? "down" : "neutral"}`}>
                              {positionDirectionLabel(item)}
                            </Badge>
                          </td>
                          <td>
                            <strong>{positionQuantityText(item, ["pos"])}</strong>
                            <small>可平 {positionQuantityText(item, ["availPos", "pos"])}</small>
                          </td>
                          <td>
                            <strong>{formatValue(positionText(item, ["avgPx"]))}</strong>
                            <small>标记 {formatValue(positionText(item, ["markPx", "last", "idxPx"]))}</small>
                          </td>
                          <td>
                            <strong className={pnlValueClass(upl)}>{formatSignedValue(upl)}</strong>
                            <small className={pnlValueClass(ratio)}>{formatSignedPercentRatio(ratio)}</small>
                          </td>
                          <td>
                            <Button variant="subtle" size="xs"
                              className="signalLogDetailButton danger"
                              type="button"
                              disabled={!closeOrder || !tradeEnabled || isClosing}
                              onClick={() => quickClosePosition(item)}
                              title={closeOrder ? `市价全平 ${closeOrder.sz} 张` : "没有可平数量"}
                            >
                              <XCircle size={13} aria-hidden="true" />
                              {isClosing ? "提交中" : "平仓"}
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </DataTable>
              </div>
            )}
          </section>

          <section className="workbenchPanel workbenchPendingPanel" aria-label="当前挂单">
            <PanelHeader
              icon={<ChartCandlestick size={17} />}
              title="当前挂单"
              meta={`${pendingOrders.length} 笔 · ${tradeSourceLabel(pendingSource)}`}
            />
            {pendingOrders.length === 0 ? (
              <EmptyState compact>当前{environmentLabel(activeEnvironment)}没有可撤销的挂单</EmptyState>
            ) : (
              <div className="workbenchTableWrap">
                <DataTable className="minimalDataTable workbenchPendingTable">
                  <thead>
                    <tr><th>时间</th><th>合约 / 订单号</th><th>方向</th><th>价格</th><th>数量(张)</th><th>状态</th><th>操作</th></tr>
                  </thead>
                  <tbody>
                    {pendingOrders.map((order, index) => {
                      const orderKey = (order.ordId || order.clOrdId || `${order.instId}-${index}`) as string;
                      const isCanceling = cancelingOrdId === orderKey;
                      return (
                        <tr key={orderKey}>
                          <td>{formatTime(order.ctime)}</td>
                          <td>
                            <strong>{order.instId ?? "--"}</strong>
                            <small title={order.clOrdId || order.ordId || ""}>ID {order.ordId || order.clOrdId || "--"}</small>
                          </td>
                          <td>{orderTradeDirectionLabel(order.side?.toLowerCase() ?? "", false)}</td>
                          <td>{formatValue(order.px)}</td>
                          <td>{formatValue(order.sz)}</td>
                          <td>
                            <span className={`orderStatus ${orderStateClass(order.state)}`}>
                              <strong>{orderStateLabel(order.state)}</strong>
                            </span>
                          </td>
                          <td>
                            <Button
                              color="red"
                              variant="light"
                              size="xs"
                              type="button"
                              disabled={isCanceling}
                              onClick={() => cancelWorkbenchOrder(order)}
                              aria-label={`撤销 ${order.instId ?? ""} 挂单 ${orderKey}`}
                            >
                              {isCanceling ? "撤销中" : "撤销"}
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </DataTable>
              </div>
            )}
          </section>
        </div>
      </section>
    </section>
  );
}

function OrdersPage({ onOpenTrade }: { onOpenTrade?: () => void }) {
  const confirmAction = useConfirmAction();
  const [settings, setSettings] = React.useState<SettingsStatus | null>(null);
  const [instruments, setInstruments] = React.useState<Instrument[]>([]);
  const [orderEvents, setOrderEvents] = React.useState<SimOrderEvent[]>([]);
  const [pendingOrders, setPendingOrders] = React.useState<PendingOrder[]>([]);
  const [pendingSource, setPendingSource] = React.useState("");
  const [cancelingOrdId, setCancelingOrdId] = React.useState("");
  const [orderPnlSummary, setOrderPnlSummary] = React.useState<{
    pageRealizedTotal: string;
    pricedCloses: number;
    closeCount: number;
    settledCloses?: number;
  } | null>(null);
  const [orderSearch, setOrderSearch] = React.useState("");
  const [orderInstId, setOrderInstId] = React.useState("");
  const [orderActionFilter, setOrderActionFilter] = React.useState("");
  const [orderStateFilter, setOrderStateFilter] = React.useState("");
  const [orderOriginFilter, setOrderOriginFilter] = React.useState<"" | "manual" | "automation">("");
  const [orderOriginCounts, setOrderOriginCounts] = React.useState({ manual: 0, automation: 0, all: 0 });
  const [orderPageIndex, setOrderPageIndex] = React.useState(1);
  const [orderPageSize, setOrderPageSize] = React.useState(20);
  const [orderPaging, setOrderPaging] = React.useState({
    limit: 20,
    offset: 0,
    hasMore: false,
    total: 0,
    page: 1,
    pageCount: 1
  });
  const [status, setStatus] = React.useState("加载中");
  const [warning, setWarning] = React.useState("");
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);
  const [switching, setSwitching] = React.useState(false);
  const loadingOrdersRef = React.useRef(false);
  const ordersRequestSeqRef = React.useRef(0);

  const activeEnvironment = settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  const orderPageCount = Math.max(1, orderPaging.pageCount || 1);
  const orderCurrentPage = Math.min(Math.max(1, orderPaging.page || orderPageIndex), orderPageCount);
  const orderRangeStart = orderPaging.total ? orderPaging.offset + 1 : 0;
  const orderRangeEnd = Math.min(orderPaging.offset + orderEvents.length, orderPaging.total);
  const instrumentOptions = React.useMemo(() => {
    const rows = instruments
      .filter((item) => (item.inst_type ?? "").toUpperCase() === "SWAP")
      .map((item) => ({ value: item.inst_id, label: item.inst_id }));
    return [{ value: "", label: "全部合约" }, ...rows];
  }, [instruments]);

  const loadSettings = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/settings/status`);
    if (!response.ok) throw new Error("设置加载失败");
    setSettings(await response.json());
  }, []);

  const loadInstruments = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/instruments?limit=2000`);
    if (!response.ok) return;
    const payload = await response.json();
    setInstruments(payload.data ?? []);
  }, []);

  const loadOrders = React.useCallback(async () => {
    const requestSeq = ordersRequestSeqRef.current + 1;
    ordersRequestSeqRef.current = requestSeq;
    loadingOrdersRef.current = true;
    try {
      const params = new URLSearchParams({
        limit: String(orderPageSize),
        offset: String((Math.max(1, orderPageIndex) - 1) * orderPageSize)
      });
      if (orderInstId) params.set("instId", orderInstId);
      if (orderSearch.trim()) params.set("q", orderSearch.trim());
      if (orderActionFilter) params.set("action", orderActionFilter);
      if (orderStateFilter) params.set("state", orderStateFilter);
      if (orderOriginFilter) params.set("origin", orderOriginFilter);
      const response = await fetch(`${API_BASE}/api/trading/orders?${params.toString()}`);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "订单加载失败");
      }
      const payload: SimOrdersResponse = await response.json();
      if (requestSeq !== ordersRequestSeqRef.current) return;
      setOrderEvents(payload.events ?? []);
      setPendingOrders(
        (payload.pending ?? []).filter(
          (order) => order.state === "live" || order.state === "partially_filled"
        )
      );
      setPendingSource(payload.source ?? "");
      setOrderPnlSummary(payload.pnlSummary ?? null);
      setOrderOriginCounts({
        manual: payload.originCounts?.manual ?? 0,
        automation: payload.originCounts?.automation ?? 0,
        all: payload.originCounts?.all ?? 0
      });
      setOrderPaging(
        payload.paging ?? {
          limit: orderPageSize,
          offset: (Math.max(1, orderPageIndex) - 1) * orderPageSize,
          hasMore: false,
          total: payload.events?.length ?? 0,
          page: orderPageIndex,
          pageCount: 1
        }
      );
      setUpdatedAt(payload.ts ?? Date.now());
      setWarning(payload.warning ?? payload.message ?? "");
      setStatus(tradeSourceLabel(payload.source));
    } catch (error) {
      if (requestSeq !== ordersRequestSeqRef.current) return;
      setWarning(error instanceof Error ? error.message : "订单加载失败");
      setOrderPnlSummary(null);
      setStatus("订单接口异常");
    } finally {
      if (requestSeq === ordersRequestSeqRef.current) {
        loadingOrdersRef.current = false;
      }
    }
  }, [orderActionFilter, orderInstId, orderOriginFilter, orderPageIndex, orderPageSize, orderSearch, orderStateFilter]);

  React.useEffect(() => {
    loadSettings().catch((error) => setWarning(error.message));
    loadInstruments().catch(() => undefined);
  }, [loadInstruments, loadSettings]);

  React.useEffect(() => {
    setOrderPageIndex(1);
  }, [orderActionFilter, orderInstId, orderOriginFilter, orderPageSize, orderSearch, orderStateFilter]);

  React.useEffect(() => {
    if (orderPageIndex > orderPageCount) {
      setOrderPageIndex(orderPageCount);
    }
  }, [orderPageCount, orderPageIndex]);

  React.useEffect(() => {
    loadOrders().catch(() => undefined);
    const refreshVisibleOrders = () => {
      if (!document.hidden) loadOrders().catch(() => undefined);
    };
    const timer = window.setInterval(refreshVisibleOrders, ORDER_POLL_MS);
    document.addEventListener("visibilitychange", refreshVisibleOrders);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshVisibleOrders);
    };
  }, [loadOrders]);

  const ordersRealtime = useRealtimeFeed({
    topics: ["orders"],
    environment: activeEnvironment,
    onSnapshotRequired: (payload) => {
      if (payload.topic === "orders") loadOrders().catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "order.update") {
        loadOrders().catch(() => undefined);
        setStatus("订单状态已实时更新");
      }
      if (payload.type === "error" || payload.type === "stale") {
        setWarning(payload.message ?? payload.warning ?? "实时通道暂不可用，已保留 REST 回退");
      }
    }
  });

  const switchEnvironment = async (environment: "simulated" | "live") => {
    if (environment === activeEnvironment) return;
    if (
      environment === "live" &&
      !(await confirmAction("确认切换到真实盘？默认只读；只有后端开启实盘交易授权时才可下单。"))
    ) {
      return;
    }
    setSwitching(true);
    setWarning("");
    try {
      const response = await fetch(`${API_BASE}/api/settings/trading-environment`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ environment })
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "交易环境切换失败");
      }
      setSettings(await response.json());
      setOrderEvents([]);
      setOrderPnlSummary(null);
      setStatus(`${environmentLabel(environment)}已切换`);
      await loadOrders();
    } catch (error) {
      setWarning(error instanceof Error ? error.message : "交易环境切换失败");
    } finally {
      setSwitching(false);
    }
  };

  const cancelPendingOrder = async (order: PendingOrder) => {
    const ordId = (order.ordId ?? "").trim();
    const clOrdId = (order.clOrdId ?? "").trim();
    if (!ordId && !clOrdId) {
      setWarning("该挂单缺少订单号，无法撤销，请在 OKX 页面处理。");
      return;
    }
    if (!settings?.tradeEnabled) {
      setWarning(tradeBlockedDetail(settings));
      return;
    }
    const liveWarning = activeEnvironment === "live" ? "\n\n注意：这会向 OKX 真实盘提交撤单请求。" : "";
    if (
      !(await confirmAction(
        `确认撤销以下挂单？\n合约：${order.instId ?? "--"}\n方向：${orderTradeDirectionLabel(order.side?.toLowerCase() ?? "", false)}\n价格：${formatValue(order.px)}\n数量：${formatValue(order.sz)} 张\n订单号：${ordId || clOrdId}${liveWarning}`
      ))
    ) {
      return;
    }
    setCancelingOrdId(ordId || clOrdId);
    setWarning("");
    try {
      const response = await fetch(`${API_BASE}/api/trading/orders/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          environment: activeEnvironment,
          instId: order.instId,
          ordId: ordId || undefined,
          clOrdId: ordId ? undefined : clOrdId
        })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "撤单失败");
      setStatus(`撤单请求已提交 · ${order.instId ?? ""}`);
      await loadOrders();
    } catch (error) {
      setWarning(error instanceof Error ? error.message : "撤单失败");
    } finally {
      setCancelingOrdId("");
    }
  };

  return (
    <section className="tradePage ordersPage">
      <PageHeader
        eyebrow="订单"
        title="订单记录"
        description={`${status}${updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}`}
        actions={
          <div className="workspaceActions">
            <div className="environmentSwitch" aria-label="交易环境切换">
              <Button type="button" variant="subtle"
                className={activeEnvironment === "simulated" ? "selected" : ""}
                onClick={() => switchEnvironment("simulated")}
                disabled={switching}
              >
                虚拟盘
              </Button>
              <Button type="button" variant="subtle"
                className={activeEnvironment === "live" ? "selected danger" : ""}
                onClick={() => switchEnvironment("live")}
                disabled={switching}
              >
                真实盘
              </Button>
            </div>
            <div className="statusPills" aria-label="订单状态">
              <Badge className={`statusPill ${ordersRealtime.connected ? "live" : "warning"}`}>
                {ordersRealtime.connected ? "实时通道" : "REST 回退"}
              </Badge>
              <Badge className="statusPill">
                {environmentLabel(activeEnvironment)}
              </Badge>
            </div>
            {onOpenTrade ? (
              <Button type="button" variant="default" className="secondaryButton" onClick={onOpenTrade} leftSection={<Send size={16} />}>
                去下单
              </Button>
            ) : null}
            <IconButton label="刷新订单" onClick={() => loadOrders().catch(() => undefined)}>
              <RefreshCw size={16} />
            </IconButton>
          </div>
        }
      />

      {warning ? <Notice tone="danger">{warning}</Notice> : null}

      <section className="ordersPanel history ordersPanelPage">
        <PanelHeader icon={<Receipt size={17} />} title="本地订单记录" meta={`${orderPaging.total} 条`} />
        <section className="tradeOrderControls" aria-label="订单记录筛选">
          <TextInput
            className="tradeOrderSearch"
            leftSection={<Search size={15} aria-hidden="true" />}
            value={orderSearch}
            onChange={(event) => setOrderSearch(event.target.value)}
            placeholder="搜索合约 / 订单号 / 错误信息"
            aria-label="搜索订单记录"
          />
          <label className="tradeOrderSelect">
            <span>合约</span>
            <Select
              aria-label="订单合约"
              value={orderInstId || null}
              onChange={(value) => setOrderInstId(value ?? "")}
              data={instrumentOptions}
              placeholder="全部合约"
              searchable
              clearable
              size="xs"
            />
          </label>
          <div className="signalLogMinimalFilter orderOriginFilter" aria-label="订单来源">
            <Button type="button" variant="subtle" size="xs" className={orderOriginFilter === "" ? "selected" : ""} onClick={() => setOrderOriginFilter("")}>
              全部来源
              {orderOriginCounts.all ? <span className="orderOriginCount">{orderOriginCounts.all}</span> : null}
            </Button>
            <Button type="button" variant="subtle" size="xs" className={orderOriginFilter === "automation" ? "selected" : ""} onClick={() => setOrderOriginFilter("automation")}>
              自动化
              {orderOriginCounts.all ? <span className="orderOriginCount">{orderOriginCounts.automation}</span> : null}
            </Button>
            <Button type="button" variant="subtle" size="xs" className={orderOriginFilter === "manual" ? "selected" : ""} onClick={() => setOrderOriginFilter("manual")}>
              手动
              {orderOriginCounts.all ? <span className="orderOriginCount">{orderOriginCounts.manual}</span> : null}
            </Button>
          </div>
          <label className="tradeOrderSelect">
            <span>动作</span>
            <Select aria-label="订单动作" value={orderActionFilter || "all"} onChange={(value) => setOrderActionFilter(value === "all" ? "" : value ?? "")}
              data={orderRecordActions.map((item) => ({ value: item.key || "all", label: item.label }))} size="xs" />
          </label>
          <label className="tradeOrderSelect">
            <span>状态</span>
            <Select aria-label="订单状态" value={orderStateFilter || "all"} onChange={(value) => setOrderStateFilter(value === "all" ? "" : value ?? "")}
              data={orderRecordStates.map((item) => ({ value: item.key || "all", label: item.label }))} size="xs" />
          </label>
        </section>
        {orderPnlSummary && orderPnlSummary.closeCount > 0 ? (
          <div className="orderPnlSummary" aria-label="本页盈亏汇总">
            <span>
              本页平仓盈亏合计
              <strong className={pnlValueClass(orderPnlNumber(orderPnlSummary.pageRealizedTotal))}>
                {formatOrderPnl(orderPnlSummary.pageRealizedTotal)} USDT
              </strong>
            </span>
            <small>
              {orderPnlSummary.pricedCloses}/{orderPnlSummary.closeCount} 笔平仓可计价
              {orderPnlSummary.settledCloses ? ` · ${orderPnlSummary.settledCloses} 笔按 OKX 账单结算` : ""}
              {" · 结算值含手续费；未结算的单据取平仓前持仓浮动盈亏估算"}
            </small>
          </div>
        ) : null}

        <section className="pendingOrdersPanel" aria-label="当前挂单">
          <PanelHeader
            icon={<ChartCandlestick size={17} />}
            title="当前挂单"
            meta={`${pendingOrders.length} 笔 · ${tradeSourceLabel(pendingSource)}`}
          />
          {pendingOrders.length === 0 ? (
            <EmptyState compact>当前{environmentLabel(activeEnvironment)}没有可撤销的挂单</EmptyState>
          ) : (
            <div className="orderTable">
              <DataTable className="orderHistoryTable pendingOrderTable">
                <thead><tr><th>时间</th><th>合约 / 订单号</th><th>方向</th><th>价格</th><th>数量(张)</th><th>已成交</th><th>状态</th><th>操作</th></tr></thead>
                <tbody>
                  {pendingOrders.map((order, index) => {
                    const orderKey = (order.ordId || order.clOrdId || `${order.instId}-${index}`) as string;
                    const isCanceling = cancelingOrdId === orderKey;
                    return (
                      <tr key={orderKey}>
                        <td>{formatTime(order.ctime)}</td>
                        <td>
                          <strong>{order.instId ?? "--"}</strong>
                          <small title={order.clOrdId || order.ordId || ""}>ID {order.ordId || order.clOrdId || "--"}</small>
                        </td>
                        <td>{orderTradeDirectionLabel(order.side?.toLowerCase() ?? "", false)}</td>
                        <td>{formatValue(order.px)}</td>
                        <td>{formatValue(order.sz)}</td>
                        <td>{formatValue(order.accFillSz ?? order.fillSz)}</td>
                        <td>
                          <span className={`orderStatus ${orderStateClass(order.state)}`}>
                            <strong>{orderStateLabel(order.state)}</strong>
                          </span>
                        </td>
                        <td>
                          <Button
                            color="red"
                            variant="light"
                            size="xs"
                            type="button"
                            disabled={isCanceling || switching}
                            onClick={() => cancelPendingOrder(order)}
                            aria-label={`撤销 ${order.instId ?? ""} 挂单 ${orderKey}`}
                          >
                            {isCanceling ? "撤销中" : "撤销"}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </DataTable>
            </div>
          )}
        </section>

        <div className="orderTable">
          <DataTable className="orderHistoryTable">
            <thead><tr><th>时间</th><th>来源</th><th>动作</th><th>合约 / 订单号</th><th>方向</th><th>价格</th><th>数量(张)</th><th>盈亏</th><th>状态</th></tr></thead>
            <tbody>
              {orderEvents.map((event, index) => {
                const pnlValue = orderPnlNumber(event.pnl_usd);
                const pnlBasis = orderPnlBasisLabel(event.pnl_basis);
                const orderRef = event.cl_ord_id || event.ord_id || "";
                const isAutomation = event.origin === "automation";
                return (
                  <tr key={`${event.ts}-${event.ord_id}-${event.cl_ord_id}-${index}`}>
                    <td>{formatTime(event.ts)}</td>
                    <td className="orderOriginCell">
                      <span className={`orderOriginTag ${isAutomation ? "automation" : "manual"}`}>
                        {isAutomation ? "自动化" : "手动"}
                      </span>
                      <small title={event.close_strategy_id ? `该仓位由策略 #${event.close_strategy_id}${event.close_strategy_name ? `（${event.close_strategy_name}）` : ""} 开出，本次平仓由手动/接口发起` : undefined}>
                        {isAutomation
                          ? event.strategy_id
                            ? `策略 #${event.strategy_id}${event.signal_id ? ` / 信号 #${event.signal_id}` : ""}`
                            : "自动化策略"
                          : event.close_strategy_id
                            ? `平 策略 #${event.close_strategy_id} 仓`
                            : "手动操作"}
                      </small>
                    </td>
                    <td>{orderActionLabel(event.action)}</td>
                    <td>
                      <strong>{event.inst_id ?? "--"}</strong>
                      <small>{orderRef ? `ID ${orderRef}` : "无订单号"}</small>
                    </td>
                    <td>{orderEventDirectionLabel(event)}</td>
                    <td>{formatValue(event.px)}</td>
                    <td>{formatValue(event.sz)}</td>
                    <td className="orderPnlCell">
                      {pnlValue === null ? (
                        <span className="pnl-neutral" title={event.pnl_note || (event.action === "close-position" ? "该笔平仓没有可结算的 OKX 账单，也没有平仓前持仓快照，无法计算盈亏。" : "开仓与撤单不产生已实现盈亏。")}>—</span>
                      ) : (
                        <>
                          <strong className={`${pnlValueClass(pnlValue)}${event.pnl_settled ? " orderPnlSettled" : ""}`}>
                            {formatOrderPnl(event.pnl_usd)} USDT
                          </strong>
                          <small>
                            {event.pnl_settled
                              ? `毛 ${formatOrderPnl(event.pnl_gross)} / 手续费 ${formatOrderPnl(event.pnl_fee)}${event.bill_count ? ` · ${event.bill_count} 笔成交` : ""}`
                              : formatOrderPnlPct(event.pnl_pct)}
                            {pnlBasis ? ` · ${pnlBasis}` : ""}
                          </small>
                        </>
                      )}
                    </td>
                    <td><span className={`orderStatus ${orderStateClass(event.state)}`} title={orderEventMessage(event) || event.message || event.code || ""}>
                      <strong>{orderStateLabel(event.state)}</strong>
                      {orderEventMessage(event) ? <small>{orderEventMessage(event)}</small> : null}
                    </span></td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
          {orderEvents.length === 0 ? <EmptyState>暂无符合条件的本地{environmentLabel(activeEnvironment)}订单记录</EmptyState> : null}
        </div>
        <div className="paginationBar tradeOrderPagination">
          <span>
            第 {orderRangeStart}-{orderRangeEnd} 条 / 共 {orderPaging.total} 条
          </span>
          <label>
            每页
            <Select aria-label="每页订单数" value={String(orderPageSize)} onChange={(value) => value && setOrderPageSize(Number(value))}
              data={orderRecordPageSizes.map((size) => ({ value: String(size), label: String(size) }))} size="xs" w={80} />
          </label>
          <div className="rowActions">
            <Button className="rowAction" variant="default" size="xs" type="button" onClick={() => setOrderPageIndex(1)} disabled={orderCurrentPage <= 1}>
              首页
            </Button>
            <Button variant="default" size="xs"
              className="rowAction"
              type="button"
              onClick={() => setOrderPageIndex((value) => Math.max(1, value - 1))}
              disabled={orderCurrentPage <= 1}
            >
              上一页
            </Button>
            <span className="pageIndex">{orderCurrentPage}/{orderPageCount}</span>
            <Button variant="default" size="xs"
              className="rowAction"
              type="button"
              onClick={() => setOrderPageIndex((value) => Math.min(orderPageCount, value + 1))}
              disabled={orderCurrentPage >= orderPageCount}
            >
              下一页
            </Button>
            <Button variant="default" size="xs"
              className="rowAction"
              type="button"
              onClick={() => setOrderPageIndex(orderPageCount)}
              disabled={orderCurrentPage >= orderPageCount}
            >
              末页
            </Button>
          </div>
        </div>
      </section>
    </section>
  );
}

function strategyInstrumentLabel(strategy: AutomationStrategy): string {
  const ids = strategy.instIds?.length ? strategy.instIds : [strategy.inst_id];
  return ids.length > 1 ? `${ids[0]} 等 ${ids.length} 个合约` : ids[0];
}

function strategyToForm(strategy: AutomationStrategy): AutomationStrategyForm {
  return {
    name: strategy.name,
    instId: strategy.inst_id,
    instIds: strategy.instIds?.length ? strategy.instIds : [strategy.inst_id],
    dailyPositionPct: strategy.dailyPositionPct ?? strategy.daily_position_pct ?? "0",
    bar: strategy.bar,
    template: strategy.template,
    executionMode: strategy.execution_mode,
    tdMode: strategy.td_mode,
    ordType: strategy.ord_type,
    sz: strategy.sz,
    fastWindow: String(strategy.fast_window),
    slowWindow: String(strategy.slow_window),
    maxPositionContracts: strategy.max_position_contracts,
    cooldownSeconds: String(strategy.cooldown_seconds),
    takeProfitPct: strategy.take_profit_pct ?? "0",
    stopLossPct: strategy.stop_loss_pct ?? "0"
  };
}

function automationFormPayload(form: AutomationStrategyForm, enabled = false) {
  return {
    name: form.name.trim(),
    enabled,
    instId: (form.instIds[0] || form.instId).trim().toUpperCase(),
    instIds: form.instIds.map((item) => item.trim().toUpperCase()).filter(Boolean),
    dailyPositionPct: form.dailyPositionPct.trim() || "0",
    bar: form.bar,
    template: form.template,
    executionMode: form.executionMode,
    tdMode: form.tdMode,
    ordType: form.ordType,
    sz: form.sz.trim(),
    fastWindow: Number(form.fastWindow),
    slowWindow: Number(form.slowWindow),
    // 单笔上限恒等于固定下单张数（后端保存时强制 sz <= maxOrderContracts）。
    // 表单不再暴露这个冗余输入，提交时直接由 sz 派生，避免填出无效组合。
    maxOrderContracts: form.sz.trim() || "1",
    maxPositionContracts: form.maxPositionContracts.trim(),
    cooldownSeconds: Number(form.cooldownSeconds),
    takeProfitPct: form.takeProfitPct.trim() || "0",
    stopLossPct: form.stopLossPct.trim() || "0"
  };
}

function FieldHint({ text, label }: { text: React.ReactNode; label: string }) {
  return (
    <Tooltip label={text} multiline w={300} withArrow position="top-start" openDelay={100} withinPortal>
      <span className="fieldHintIcon" role="img" tabIndex={0} aria-label={label} title="">
        i
      </span>
    </Tooltip>
  );
}

function CleanAutomationPage({
  initialInstId = "BTC-USDT-SWAP",
  initialEditStrategyId = null,
  initialCreate = false,
  onCreateConsumed,
  onEditConsumed,
  onOpenStrategies,
  onOpenSignals,
  onOpenLlm,
  onOpenSignalDetail
}: {
  initialInstId?: string;
  initialEditStrategyId?: number | null;
  initialCreate?: boolean;
  onCreateConsumed?: () => void;
  onEditConsumed?: () => void;
  onOpenStrategies: () => void;
  onOpenSignals: () => void;
  onOpenLlm: () => void;
  onOpenSignalDetail: (signalId: number) => void;
}) {
  const [strategies, setStrategies] = React.useState<AutomationStrategy[]>([]);
  const [signals, setSignals] = React.useState<AutomationSignal[]>([]);
  const [alerts, setAlerts] = React.useState<AutomationAlert[]>([]);
  const [automationStatus, setAutomationStatus] = React.useState<AutomationStatus | null>(null);
  const [selectedId, setSelectedId] = React.useState<number | null>(null);
  const [form, setForm] = React.useState<AutomationStrategyForm>(defaultAutomationForm);
  const [status, setStatus] = React.useState("加载中");
  const [view, setView] = React.useState<"overview" | "strategy" | "create">("overview");
  // 处于「新建」流程时禁止自动选中已有策略，否则空白表单会被第一条策略覆盖。
  const createIntentRef = React.useRef(false);
  const [riskPreview, setRiskPreview] = React.useState<AutomationRiskPreview | null>(null);
  const [riskStatus, setRiskStatus] = React.useState("等待检查");
  const [riskLoading, setRiskLoading] = React.useState(false);
  const [showPassedChecks, setShowPassedChecks] = React.useState(false);
  const [loadError, setLoadError] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [saveNotice, setSaveNotice] = React.useState("");
  const [customInstId, setCustomInstId] = React.useState("");
  // 合约是低频设置：默认折叠成一行摘要，点「修改」再展开快捷选择与输入框。
  const [instEditorOpen, setInstEditorOpen] = React.useState(false);
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);
  const [automationEquity, setAutomationEquity] = React.useState<AutomationEquity | null>(null);
  const [equityLoading, setEquityLoading] = React.useState(false);
  const [equityError, setEquityError] = React.useState("");

  const selectedStrategy = React.useMemo(
    () => strategies.find((item) => item.id === selectedId) ?? null,
    [selectedId, strategies]
  );
  const activeStrategy = selectedStrategy ?? strategies.find((item) => item.enabled) ?? strategies[0] ?? null;
  const latestSignal = activeStrategy ? latestStrategySignal(signals, activeStrategy.id) : signals[0] ?? null;
  const recentAlerts = alerts.slice(0, 4);
  const submittedSignals = signals.filter((item) => item.decision === "submitted").length;
  const riskChecks = riskPreview?.checks ?? [];
  const blockingCheck = riskChecks.find((item) => item.status === "block");
  const blockingChecks = riskChecks.filter((item) => item.status === "block");
  const warningChecks = riskChecks.filter((item) => item.status === "warn");
  const passedChecks = riskChecks.filter((item) => item.status !== "block" && item.status !== "warn");
  const hasStrategies = strategies.length > 0;
  const hasEnabledStrategy = strategies.some((item) => item.enabled);
  const hasUnconfirmedAlerts = alerts.some((item) => item.active);
  // 引擎在 simulated_auto 模式下会于模拟盘自动下单；没有策略时不能沿用"只记录信号"之类结论。
  const decisionTone = hasStrategies ? (riskPreview?.allowed ? "ok" : blockingCheck ? "block" : "warn") : "warn";
  const decisionTitle = !hasStrategies
    ? "尚未创建策略"
    : riskPreview?.allowed
      ? "可以自动下单"
      : blockingCheck
        ? "暂不能自动下单"
        : riskPreview
          ? "当前只记录信号"
          : "启用检查未完成";
  const decisionMessage = !hasStrategies
    ? "引擎正在运行，但当前没有策略会产生信号。创建并启用策略后，才会按风控规则在模拟盘自动执行；实盘始终隔离。"
    : riskPreview?.message || blockingCheck?.message || riskStatus;
  const equityPct = Number(form.dailyPositionPct);
  const hasEquityPct = Number.isFinite(equityPct) && equityPct > 0 && equityPct <= 100;
  const equityHint = equityLoading && !automationEquity
    ? "正在读取模拟盘账户金额…"
    : equityError || (!automationEquity
      ? "账户金额尚未读取"
      : automationEquity.available
        ? ""
        : automationEquity.message || "模拟盘账户金额不可用，启用每日仓位% 后开仓会被拦截");
  const equityHintTone = equityError || automationEquity?.available === false ? "warn" : "muted";
  // 「只提醒」只记录信号不下单，引擎也不会检查止盈止损（automation_exit_signal 仅对
  // simulated_auto 生效），因此这两项在只提醒模式下必须禁用并说明，否则会误导。
  const exitsDisabled = form.executionMode !== "simulated_auto";
  const barIntervalLabel = automationBarOptions.find((item) => item.key === form.bar)?.label ?? form.bar;
  const barCadence = automationBarCadence[form.bar] ?? { cadence: "按周期", perDay: 0 };
  const strategyContractCount = Math.max(1, form.instIds.length);
  const dailyEvalLimit = barCadence.perDay * strategyContractCount;
  const saveStateText = selectedStrategy
    ? selectedStrategy.enabled
      ? "已启动，保存后继续运行"
      : "已保存的策略仍处于暂停状态"
    : "新策略默认先保存为暂停";

  const checkTone = (value?: string) => value === "pass" ? "ok" : value === "block" ? "block" : "warn";
  const renderRiskGroup = (label: string, items: AutomationRiskCheck[]) => (
    <div className="automationCheckGroup" key={label}>
      <div className="automationCheckGroupLabel">{label} · {items.length} 项</div>
      {items.map((item) => (
        <div className="cleanListRow" key={item.key}>
          <span className={`cleanStatusDot ${checkTone(item.status)}`} />
          <div>
            <strong>{item.label}</strong>
            <small title={item.message}>{item.message}</small>
          </div>
          <Badge className={`cleanTag ${checkTone(item.status)}`}>{riskStatusLabel(item.status)}</Badge>
        </div>
      ))}
    </div>
  );
  const decisionToneForSignal = (decision?: string) => {
    const klass = automationDecisionClass(decision);
    if (klass === "down") return "block";
    if (klass === "up") return "ok";
    return "warn";
  };

  const updateForm = (key: keyof AutomationStrategyForm, value: string) => {
    setSaveNotice("");
    setForm((current) => ({ ...current, [key]: value }));
  };

  const setInstIds = (next: string[]) => {
    const normalized = Array.from(new Set(next.map((item) => item.trim().toUpperCase()).filter(Boolean))).slice(0, MAX_AUTOMATION_INST_IDS);
    if (!normalized.length) {
      setStatus("请至少保留一个合约");
      return;
    }
    setSaveNotice("");
    setStatus("");
    setForm((current) => ({ ...current, instIds: normalized, instId: normalized[0] }));
  };

  const addCustomInstrument = () => {
    const value = customInstId.trim().toUpperCase();
    if (!value) return;
    if (!value.endsWith("-SWAP")) {
      setStatus("合约代码需以 -SWAP 结尾，例如 ETH-USDT-SWAP");
      return;
    }
    if (form.instIds.includes(value)) {
      setCustomInstId("");
      return;
    }
    if (form.instIds.length >= MAX_AUTOMATION_INST_IDS) {
      setStatus(`一条策略最多选择 ${MAX_AUTOMATION_INST_IDS} 个合约`);
      return;
    }
    setInstIds([...form.instIds, value]);
    setCustomInstId("");
  };

  const togglePopularInstrument = (value: string) => {
    setInstIds(
      form.instIds.includes(value)
        ? form.instIds.filter((item) => item !== value)
        : [...form.instIds, value]
    );
  };

  React.useEffect(() => {
    const normalized = initialInstId.trim().toUpperCase();
    if (!normalized.endsWith("-SWAP")) return;
    setForm((current) => {
      if (current.instIds.length > 1) return current;
      if (current.instIds[0] === normalized && current.instId === normalized) return current;
      return { ...current, instId: normalized, instIds: [normalized] };
    });
  }, [initialInstId]);

  const updateOrderContracts = (value: string) => {
    setForm((current) => {
      const next = { ...current, sz: value };
      const numeric = Number(value);
      // 最多持仓是真实生效的累计约束：调大每次下单时同步抬高，避免保存成功
      // 却每轮都被「持仓上限」拦截。单笔上限已由 sz 派生，不再需要联动。
      if (Number.isFinite(numeric) && numeric > 0) {
        const maxPosition = Number(current.maxPositionContracts);
        if (!Number.isFinite(maxPosition) || maxPosition < numeric) next.maxPositionContracts = value;
      }
      return next;
    });
  };

  const automationPayload = React.useCallback(() => ({
    ...automationFormPayload(form, selectedStrategy?.enabled ?? false),
    strategyId: selectedStrategy?.id ?? 0
  }), [form, selectedStrategy]);

  const loadAutomation = React.useCallback(async () => {
    try {
      const [strategyResponse, signalResponse, alertResponse, statusResponse] = await Promise.all([
        fetch(`${API_BASE}/api/automation/strategies`),
        fetch(`${API_BASE}/api/automation/signals?limit=100`),
        fetch(`${API_BASE}/api/automation/alerts?limit=20`),
        fetch(`${API_BASE}/api/automation/status`)
      ]);
      if (!strategyResponse.ok || !signalResponse.ok || !alertResponse.ok || !statusResponse.ok) {
        throw new Error("接口返回异常");
      }
      const strategyPayload = await strategyResponse.json();
      const signalPayload = await signalResponse.json();
      const alertPayload = await alertResponse.json();
      const statusPayload = await statusResponse.json();
      const rows: AutomationStrategy[] = strategyPayload.data ?? [];
      setStrategies(rows);
      setSignals(signalPayload.data ?? []);
      setAlerts(alertPayload.data ?? []);
      setAutomationStatus(statusPayload);
      if (!createIntentRef.current) {
        setSelectedId((current) => current ?? rows.find((item) => item.enabled)?.id ?? rows[0]?.id ?? null);
      }
      setUpdatedAt(Date.now());
      setLoadError("");
      setStatus("自动交易数据已更新");
    } catch {
      setLoadError("自动交易数据未能加载，页面内容可能不是最新。请点击「重试」重新读取；若持续失败，请检查后端服务是否正常。");
      setStatus("自动交易数据加载失败");
    }
  }, []);

  const loadRiskPreview = React.useCallback(async () => {
    setRiskLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(automationPayload())
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "启用检查失败");
      setRiskPreview(payload.data as AutomationRiskPreview);
      setRiskStatus("启用检查已更新");
    } catch {
      setRiskPreview(null);
      setRiskStatus("启用检查未能完成，页面不会据此判断能否下单。请点击「重试」；若持续失败，请检查后端服务与模拟盘凭证。");
    } finally {
      setRiskLoading(false);
    }
  }, [automationPayload]);

  // 每日仓位% 的金额口径必须与后端风控一致，因此只读 /api/automation/equity（模拟盘）。
  // 输入做 debounce，且只在创建/编辑视图请求，避免总览页产生无谓的账户请求。
  const loadAutomationEquity = React.useCallback(async (force = false) => {
    setEquityLoading(true);
    try {
      const params = new URLSearchParams({
        dailyPositionPct: form.dailyPositionPct.trim() || "0",
        strategyId: String(selectedStrategy?.id ?? 0)
      });
      if (force) params.set("force", "true");
      const response = await fetch(`${API_BASE}/api/automation/equity?${params.toString()}`);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "账户金额读取失败");
      setAutomationEquity(payload.data as AutomationEquity);
      setEquityError("");
    } catch {
      setEquityError("模拟盘账户金额未能读取，启用每日仓位% 后风控会按不可用处理并拦截开仓。");
    } finally {
      setEquityLoading(false);
    }
  }, [form.dailyPositionPct, selectedStrategy?.id]);

  React.useEffect(() => {
    if (view !== "create") return;
    const timer = window.setTimeout(() => { void loadAutomationEquity(); }, 300);
    return () => window.clearTimeout(timer);
  }, [view, loadAutomationEquity]);

  const pauseAutomation = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/pause`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "用户手动暂停自动交易" })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "暂停失败");
      setStatus("自动交易已暂停");
      await loadAutomation();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "暂停失败");
    } finally {
      setSaving(false);
    }
  };

  const resumeAutomation = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/resume`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "恢复失败");
      setStatus("自动交易已恢复");
      await loadAutomation();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "恢复失败");
    } finally {
      setSaving(false);
    }
  };

  const acknowledgeAlert = async (alert: AutomationAlert) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/alerts/${alert.id}/ack`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "确认告警失败");
      setStatus("告警已确认");
      await loadAutomation();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "确认告警失败");
    } finally {
      setSaving(false);
    }
  };

  React.useEffect(() => {
    loadAutomation().catch(() => setStatus("自动交易数据加载失败"));
    const timer = window.setInterval(() => {
      if (!document.hidden) loadAutomation().catch(() => undefined);
    }, 10000);
    return () => window.clearInterval(timer);
  }, [loadAutomation]);

  const cleanAutomationRealtime = useRealtimeFeed({
    topics: ["automation.status", "automation.alert", "automation.signal"],
    onSnapshotRequired: () => {
      loadAutomation().catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "automation.status" || payload.type === "automation.alert" || payload.type === "automation.signal") {
        loadAutomation().catch(() => undefined);
        setStatus("自动交易实时事件已同步");
      }
      if (payload.type === "error" || payload.type === "stale") {
        setStatus(payload.message ?? "实时通道暂不可用，已保留 REST 回退");
      }
    }
  });

  React.useEffect(() => {
    if (!initialEditStrategyId || !strategies.length) return;
    const strategy = strategies.find((item) => item.id === initialEditStrategyId);
    if (!strategy) return;
    setSelectedId(strategy.id);
    setForm(strategyToForm(strategy));
    setRiskPreview(null);
    setRiskStatus("等待检查");
    setView("create");
    onEditConsumed?.();
  }, [initialEditStrategyId, onEditConsumed, strategies]);

  React.useEffect(() => {
    if (view !== "create" && selectedStrategy) {
      setForm(strategyToForm(selectedStrategy));
    }
  }, [selectedStrategy, view]);

  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      loadRiskPreview().catch(() => undefined);
    }, 500);
    return () => window.clearTimeout(timer);
  }, [loadRiskPreview]);

  const saveStrategy = async (updateExisting: boolean, startAfterSave = false) => {
    setSaving(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/automation/strategies${updateExisting && selectedStrategy ? `/${selectedStrategy.id}` : ""}`,
        {
          method: updateExisting && selectedStrategy ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(automationFormPayload(form, selectedStrategy?.enabled ?? false))
        }
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "策略保存失败");
      const savedStrategy = payload.data as AutomationStrategy | undefined;
      const savedId = savedStrategy?.id ?? selectedId;
      createIntentRef.current = false;
      setSelectedId(savedId);
      if (startAfterSave && savedId && !savedStrategy?.enabled) {
        const toggleResponse = await fetch(`${API_BASE}/api/automation/strategies/${savedId}/toggle`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: true })
        });
        const togglePayload = await toggleResponse.json().catch(() => ({}));
        if (!toggleResponse.ok) throw new Error(togglePayload.detail ?? "策略已保存，但启动失败");
        setStatus("策略已保存并启动");
        setSaveNotice("策略已保存并启动。若执行方式为模拟盘自动，满足风控和信号后才会提交订单。");
      } else {
        const pausedHint = savedStrategy?.enabled ? "策略已保存，当前保持运行。" : "策略已保存，但仍处于暂停状态。";
        setStatus(updateExisting ? "策略已更新" : "策略已创建");
        setSaveNotice(pausedHint);
      }
      await loadAutomation();
    } catch (error) {
      const message = error instanceof Error ? error.message : "策略保存失败";
      setStatus(message);
      setSaveNotice(message);
    } finally {
      setSaving(false);
    }
  };

  const editStrategy = (strategy: AutomationStrategy) => {
    createIntentRef.current = false;
    setSelectedId(strategy.id);
    setForm(strategyToForm(strategy));
    setView("create");
  };

  const toggleStrategy = async (strategy: AutomationStrategy) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/strategies/${strategy.id}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !strategy.enabled })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "策略状态更新失败");
      setStatus(!strategy.enabled ? "策略已启动" : "策略已暂停");
      await loadAutomation();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "策略状态更新失败");
    } finally {
      setSaving(false);
    }
  };

  const runStrategy = async (strategy: AutomationStrategy) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/strategies/${strategy.id}/run`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "策略运行失败");
      setStatus(payload.data ? "策略已运行一次" : "策略没有产生新记录");
      await loadAutomation();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "策略运行失败");
    } finally {
      setSaving(false);
    }
  };

  const resetForCreate = () => {
    createIntentRef.current = true;
    setSelectedId(null);
    setForm(defaultAutomationForm);
    setView("create");
  };

  React.useEffect(() => {
    if (!initialCreate) return;
    resetForCreate();
    onCreateConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCreate, onCreateConsumed]);

  return (
    <section className="automationPage cleanAutomationPage">
      <div className="workspaceHeader cleanAutomationHeader">
        <div>
          <span className="eyebrow">自动交易</span>
          <h1>当前状态</h1>
          <p>{status}{updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}</p>
          {status === "加载中" ? <DataLoadingState label="正在读取自动交易状态" compact /> : null}
        </div>
        <div className="workspaceActions">
          <div className="statusPills" aria-label="自动交易状态">
            <Badge className={`statusPill ${automationStatus?.running ? "live" : "warning"}`}>
              引擎{automationStatus?.running ? "运行中" : "未运行"}
            </Badge>
            {automationStatus?.globalStateAvailable === false || automationStatus?.globalPaused || automationStatus?.circuitBreakerActive ? (
              <Badge className="statusPill warning">{automationGlobalStateLabel(automationStatus)}</Badge>
            ) : null}
            {(automationStatus?.alertCount ?? 0) > 0 ? (
              <Badge className="statusPill warning">告警 {automationStatus?.alertCount}</Badge>
            ) : null}
          </div>
          <Button variant="default" size="xs" className="secondaryButton slim" type="button" onClick={pauseAutomation} disabled={saving || Boolean(automationStatus?.globalPaused)}>
            <Pause size={15} aria-hidden="true" />
            暂停
          </Button>
          <Button
            variant="default"
            size="xs"
            className="secondaryButton slim"
            type="button"
            onClick={resumeAutomation}
            disabled={saving || (!automationStatus?.globalPaused && !automationStatus?.circuitBreakerActive)}
            title={!automationStatus?.globalPaused && !automationStatus?.circuitBreakerActive ? "仅在全局暂停或熔断后需要人工恢复" : undefined}
          >
            <Play size={15} aria-hidden="true" />
            恢复
          </Button>
          <IconButton
            label="刷新自动交易"
            onClick={() => {
              loadAutomation().catch(() => setStatus("自动交易数据加载失败"));
              loadRiskPreview().catch(() => undefined);
            }}
          >
            <RefreshCw size={16} />
          </IconButton>
        </div>
      </div>

      {automationStatus?.warning ? <Notice tone="warning">{automationStatus.warning}</Notice> : null}
      {automationStatus?.globalStateAvailable === false && automationStatus?.pauseReason ? (
        <Notice tone="warning">{automationStatus.pauseReason}</Notice>
      ) : null}
      {loadError ? (
        <Notice tone="warning">
          <span>{loadError}</span>
          <Button variant="subtle" size="xs" className="rowAction" type="button" onClick={() => { void loadAutomation(); void loadRiskPreview(); }}>重试</Button>
        </Notice>
      ) : null}

      {view === "overview" ? (
        <section className="cleanAutomationView">
          <section className={`cleanDecisionPanel ${decisionTone}`}>
            <div>
              <h2>{decisionTitle}</h2>
              <p>{decisionMessage}</p>
              {!hasEnabledStrategy ? (
                <div className="cleanDecisionHint">
                  <span>
                    {hasStrategies
                      ? `${strategies.length} 条策略都处于暂停，启用后才会产生信号。`
                      : "还没有策略，先创建一条。"}
                  </span>
                  <Button
                    variant="subtle"
                    size="xs"
                    className="secondaryButton"
                    type="button"
                    onClick={hasStrategies ? onOpenStrategies : resetForCreate}
                  >
                    {hasStrategies ? "查看策略" : "创建策略"}
                  </Button>
                </div>
              ) : null}
            </div>
            <div className="cleanInlineMetrics" aria-label="自动交易关键指标">
              <div className="cleanInlineMetric">
                <span>活跃策略</span>
                <strong>{automationStatus?.enabledCount ?? strategies.filter((item) => item.enabled).length}/{automationStatus?.strategyCount ?? strategies.length}</strong>
              </div>
              <div className="cleanInlineMetric">
                <span>最近信号</span>
                <strong className={latestSignal ? automationActionClass(latestSignal.action) : ""}>{latestSignal ? automationActionLabel(latestSignal.action) : "--"}</strong>
              </div>
              <div className="cleanInlineMetric">
                <span>今日提交</span>
                <strong>{submittedSignals}</strong>
              </div>
            </div>
          </section>

          <section className="cleanPanel">
            <PanelHeader
              icon={<Bot size={17} />}
              title="活跃策略"
              meta={activeStrategy ? `#${activeStrategy.id}` : "暂无"}
              action={
                <Group gap={6} className="strategyHeaderActions">
                  <Button className="primaryButton" size="xs" type="button" onClick={resetForCreate}>新建策略</Button>
                  <Button variant="subtle" size="xs" className="secondaryButton" type="button" onClick={onOpenStrategies}>全部策略</Button>
                </Group>
              }
            />
            {activeStrategy ? (
              <div className="cleanStrategyDetail">
                <div className="cleanStrategyHead">
                  <div className="cleanStrategyTitle">
                    <strong title={activeStrategy.name}>{activeStrategy.name}</strong>
                    <Badge className={`statusPill ${activeStrategy.enabled ? "live" : "warning"}`}>{automationEnabledLabel(activeStrategy.enabled)}</Badge>
                  </div>
                  <span className="cleanStrategyMeta">
                    {strategyInstrumentLabel(activeStrategy)} · {automationBarLabel(activeStrategy.bar)} · {automationTemplateLabel(activeStrategy.template)} · {automationExecutionModeLabel(activeStrategy.execution_mode)}
                    {` · 每次 ${formatValue(activeStrategy.sz)} 张 · 持仓上限 ${formatValue(activeStrategy.max_position_contracts)} 张 · 止盈/止损 ${formatValue(activeStrategy.take_profit_pct ?? "0")}% / ${formatValue(activeStrategy.stop_loss_pct ?? "0")}%`}
                  </span>
                </div>
                <div className="cleanActionRow">
                  <Button variant="default" className="secondaryButton" type="button" onClick={() => editStrategy(activeStrategy)} disabled={saving}>编辑策略</Button>
                  <Button variant="default" className="secondaryButton" type="button" onClick={() => runStrategy(activeStrategy)} disabled={saving}>
                    <Play size={13} />
                    运行一次
                  </Button>
                  <Button className="primaryButton" type="button" onClick={() => toggleStrategy(activeStrategy)} disabled={saving}>
                    {activeStrategy.enabled ? <Pause size={13} /> : <Play size={13} />}
                    {activeStrategy.enabled ? "暂停" : "启动"}
                  </Button>
                </div>
              </div>
            ) : (
              <EmptyState>暂无策略，先创建第一条自动交易策略</EmptyState>
            )}
          </section>

          <section className="cleanAutomationGrid">
            <div className="cleanAutomationColumn">
              <section className="cleanPanel">
                <PanelHeader
                  icon={<ShieldCheck size={17} />}
                  title="启用检查"
                  meta={riskLoading ? "检查中" : !riskPreview ? "未完成" : blockingCheck ? "有阻塞" : riskPreview.allowed ? "通过" : `${riskChecks.length} 项`}
                  action={
                    <Button variant="subtle" size="xs" className="rowAction" type="button" onClick={blockingCheck?.key === "llm" ? onOpenLlm : loadRiskPreview} disabled={riskLoading}>
                      {blockingCheck?.key === "llm" ? "去配置" : riskPreview ? "刷新" : "重试"}
                    </Button>
                  }
                />
                <div className="cleanList">
                  {riskLoading && !riskPreview ? (
                    <DataLoadingState label="正在检查启用条件" compact />
                  ) : riskPreview ? (
                    <>
                      {blockingChecks.length ? renderRiskGroup("阻塞项", blockingChecks) : null}
                      {warningChecks.length ? renderRiskGroup("需关注", warningChecks) : null}
                      {passedChecks.length ? (
                        <div className="automationCheckGroup">
                          <Button
                            variant="subtle"
                            size="xs"
                            className="rowAction automationCheckToggle"
                            type="button"
                            aria-expanded={showPassedChecks}
                            onClick={() => setShowPassedChecks((current) => !current)}
                          >
                            {showPassedChecks ? "收起" : "展开"}已通过 {passedChecks.length} 项
                          </Button>
                          {showPassedChecks ? renderRiskGroup("已通过", passedChecks) : null}
                        </div>
                      ) : null}
                    </>
                  ) : (
                    <EmptyState compact className="automationEmptyState">
                      <strong>启用检查未完成</strong>
                      <small>{riskStatus}</small>
                      <Button variant="subtle" size="xs" className="rowAction" type="button" onClick={loadRiskPreview}>重试</Button>
                    </EmptyState>
                  )}
                </div>
              </section>

              {recentAlerts.length ? (
                <section className="cleanPanel automationAlertPanel">
                  <PanelHeader
                    icon={<ShieldAlert size={17} />}
                    title="最近告警"
                    meta={`${recentAlerts.length}/${alerts.length}`}
                    action={<Button variant="subtle" size="xs" className="rowAction" type="button" onClick={() => loadAutomation().catch(() => setStatus("自动交易数据加载失败"))}>刷新</Button>}
                  />
                  <div className="cleanList">
                    {recentAlerts.map((alert) => (
                      <div className="cleanListRow automationAlertRow" key={alert.id}>
                        <span className={`cleanStatusDot ${automationAlertSeverityClass(alert.severity)}`} />
                        <div>
                          <strong>{automationAlertSourceLabel(alert.source)} · {automationAlertSeverityLabel(alert.severity)}</strong>
                          <small title={alert.message}>{alert.message} · {formatTime(alert.ts)}</small>
                        </div>
                        <span className="compactRowActions">
                          <Badge className={`cleanTag ${automationAlertSeverityClass(alert.severity)}`}>{automationAlertStateLabel(alert)}</Badge>
                          {alert.signal_id ? (
                            <ActionIcon className="signalLogIconButton" type="button" onClick={() => onOpenSignalDetail(alert.signal_id as number)} title="查看信号详情" aria-label="查看信号详情" variant="subtle">
                              <BookOpen size={16} />
                            </ActionIcon>
                          ) : null}
                          {alert.active ? (
                            <Button className="signalLogDetailButton" variant="subtle" size="xs" type="button" onClick={() => acknowledgeAlert(alert)} disabled={saving}>
                              确认
                            </Button>
                          ) : null}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}
            </div>

            <section className="cleanPanel">
              <PanelHeader
                icon={<Activity size={17} />}
                title="最近动作"
                meta={`${signals.length} 条`}
                action={<Button variant="subtle" size="xs" className="rowAction" type="button" onClick={onOpenSignals}>日志</Button>}
              />
              <div className="cleanList">
                {signals.slice(0, 5).length ? (
                  signals.slice(0, 5).map((signal) => (
                    <div className="cleanListRow" key={signal.id}>
                      <span className={`cleanStatusDot ${decisionToneForSignal(signal.decision)}`} />
                      <div>
                        <strong>{signal.inst_id} {automationActionLabel(signal.action)}</strong>
                        <small title={signal.message || signal.reason || formatTime(signal.ts)}>
                          {signal.message || signal.reason || formatTime(signal.ts)} · {formatClockSecond(signal.ts)}
                        </small>
                      </div>
                      <Badge className={`cleanTag ${decisionToneForSignal(signal.decision)}`}>{automationDecisionLabel(signal.decision)}</Badge>
                    </div>
                  ))
                ) : (
                  <EmptyState compact className="automationEmptyState">
                    <strong>还没有策略信号</strong>
                    <small>{hasStrategies ? "策略启用后，每次运行都会在这里记录信号、风控拦截与下单结果。" : "创建并启用策略后，每次运行都会在这里留下记录。"}</small>
                    <Button variant="subtle" size="xs" className="rowAction" type="button" onClick={onOpenSignals}>查看全部日志</Button>
                  </EmptyState>
                )}
              </div>
            </section>
          </section>
        </section>
      ) : null}

      {view === "create" ? (
        <section className="cleanAutomationView cleanAutomationEditor">
          <section className="cleanPanel">
            <PanelHeader
              icon={<Bot size={17} />}
              title={selectedStrategy ? "编辑策略" : "创建策略"}
              meta={riskPreview?.allowed ? "可启用" : "需检查"}
              action={
                <Group gap={6}>
                  <Button variant="subtle" size="xs" className="secondaryButton" type="button" onClick={onOpenStrategies} disabled={saving}>返回策略</Button>
                  <Button variant="subtle" size="xs" className="secondaryButton" type="button" onClick={resetForCreate} disabled={saving}>新建</Button>
                </Group>
              }
            />
            <div className="cleanStrategyForm">
              <label className="fieldBlock automationNameField">
                <span>策略名称</span>
                <TextInput value={form.name} onChange={(event) => updateForm("name", event.target.value)} />
              </label>
              <div className="fieldBlock automationInstrumentField">
                <span id="automationInstrumentLabel">
                  合约 · 已选 {form.instIds.length}/{MAX_AUTOMATION_INST_IDS}
                  <Button
                    variant="subtle"
                    size="xs"
                    className="automationInstrumentToggle"
                    type="button"
                    onClick={() => setInstEditorOpen((value) => !value)}
                    aria-expanded={instEditorOpen}
                  >
                    {instEditorOpen ? "收起" : "修改"}
                  </Button>
                </span>
                <div className="automationInstrumentChips" role="group" aria-labelledby="automationInstrumentLabel">
                  {form.instIds.length ? form.instIds.map((item) => (
                    <UnstyledButton
                      key={item}
                      type="button"
                      className="automationInstrumentChip selected"
                      aria-pressed={true}
                      aria-label={`移除合约 ${item}`}
                      title={`移除 ${item}`}
                      onClick={() => setInstIds(form.instIds.filter((value) => value !== item))}
                    >
                      {item}<span aria-hidden="true">×</span>
                    </UnstyledButton>
                  )) : <span className="automationInstrumentEmpty">尚未选择合约</span>}
                </div>
                {instEditorOpen ? (
                <>
                <div className="automationInstrumentQuick" role="group" aria-label="常用合约快捷选择">
                  {AUTOMATION_POPULAR_INST_IDS.map((item) => (
                    <UnstyledButton
                      key={item}
                      type="button"
                      className={`automationInstrumentOption ${form.instIds.includes(item) ? "selected" : ""}`}
                      aria-pressed={form.instIds.includes(item)}
                      onClick={() => togglePopularInstrument(item)}
                    >
                      {item.replace("-USDT-SWAP", "")}
                    </UnstyledButton>
                  ))}
                </div>
                <div className="automationInstrumentAddRow">
                  <TextInput
                    aria-label="添加自定义合约代码"
                    size="xs"
                    placeholder="输入合约代码，如 ETH-USDT-SWAP"
                    value={customInstId}
                    onChange={(event) => setCustomInstId(event.target.value.toUpperCase())}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        addCustomInstrument();
                      }
                    }}
                  />
                  <Button variant="default" size="xs" className="secondaryButton" type="button" onClick={addCustomInstrument}>添加</Button>
                </div>
                </>
                ) : null}
              </div>
              <div className="automationTripleRow">
                <label className="fieldBlock">
                  <span>
                    判断方式
                    <FieldHint
                      label="判断方式说明"
                      text={form.template === "llm_direct"
                        ? `AI 读 K 线、持仓与大盘情绪，输出多空 / 观望；置信度低于 ${automationStatus?.llmMinConfidence ?? 70} 不下单。LLM 每根 K 线调用 1 次，当前 ${strategyContractCount} 合约 ≈ ${dailyEvalLimit} 次/天。`
                        : `MA${form.fastWindow} 上穿 / 下穿 MA${form.slowWindow} 出多 / 空；只在交叉那根收盘 K 线评估，窗口沿用已保存值。`}
                    />
                  </span>
                  <Select value={form.template} onChange={(value) => value && updateForm("template", value)} data={automationTemplateOptions.map((item) => ({ value: item.key, label: item.label }))} />
                </label>
                <label className="fieldBlock">
                  <span>
                    执行方式
                    <FieldHint
                      label="执行方式说明"
                      text={form.executionMode === "simulated_auto"
                        ? "风控通过后模拟盘自动下单，实盘永不自动执行；需要模拟盘 API 凭证与交易开关。"
                        : "只记录信号，不下单、不检查止盈止损。"}
                    />
                  </span>
                  <Select value={form.executionMode} onChange={(value) => value && updateForm("executionMode", value)} data={automationExecutionModeOptions.map((item) => ({ value: item.key, label: item.label }))} />
                </label>
                <label className="fieldBlock automationBarField">
                  <span>
                    信号周期
                    <FieldHint
                      label="信号周期说明"
                      text={`${form.bar}（${barIntervalLabel}）：${barCadence.cadence}评估 1 次，单合约 ≤${barCadence.perDay} 次/天。评估上限（次/天/合约）：1m 1440 / 5m 288 / 15m 96 / 1H 24。周期越大信号越少越稳；止盈止损不受周期影响，仍每 10 秒检查。`}
                    />
                  </span>
                  <Select value={form.bar} onChange={(value) => value && updateForm("bar", value)} data={automationBarOptions.map((item) => ({ value: item.key, label: item.label }))} />
                </label>
              </div>
              <div className="automationNumberRow">
                <label className="fieldBlock">
                  <span>每次下单</span>
                  <TextInput inputMode="decimal" value={form.sz} onChange={(event) => updateOrderContracts(event.target.value)} />
                </label>
                <label className="fieldBlock">
                  <span>最多持仓</span>
                  <TextInput inputMode="decimal" value={form.maxPositionContracts} onChange={(event) => updateForm("maxPositionContracts", event.target.value)} />
                </label>
                <label className="fieldBlock">
                  <span>
                    止盈%
                    <FieldHint
                      label="止盈口径"
                      text="按价格变动百分比判定：开仓均价与标记价格对比，不乘杠杆（20 倍杠杆下价格反向 2% 即触发 2%）；0 表示关闭该项。命中后引擎在约 10 秒内的下一轮轮询优先于新开仓信号市价全平，仅模拟盘生效。默认不在 OKX 挂条件单；仅当后端开启交易所侧兜底开关时，才会在开仓成交后附带同口径条件单作进程停止时的兜底。"
                    />
                  </span>
                  <TextInput
                    inputMode="decimal"
                    value={form.takeProfitPct}
                    onChange={(event) => updateForm("takeProfitPct", event.target.value)}
                    disabled={exitsDisabled}
                    title={exitsDisabled ? "只提醒模式不会自动平仓，止盈设置不生效" : "按价格变动百分比判定，不含杠杆；0 表示不启用"}
                  />
                </label>
                <label className="fieldBlock">
                  <span>
                    止损%
                    <FieldHint
                      label="止损口径"
                      text="按价格变动百分比判定：开仓均价与标记价格对比，不乘杠杆；0 表示关闭该项。命中后约 10 秒内的下一轮轮询会市价全平，仅模拟盘生效。默认不挂交易所条件单；后端开启兜底开关后成交时会附带同口径条件单。"
                    />
                  </span>
                  <TextInput
                    inputMode="decimal"
                    value={form.stopLossPct}
                    onChange={(event) => updateForm("stopLossPct", event.target.value)}
                    disabled={exitsDisabled}
                    title={exitsDisabled ? "只提醒模式不会自动平仓，止损设置不生效" : "按价格变动百分比判定，不含杠杆；0 表示不启用"}
                  />
                </label>
              </div>
              <label className="fieldBlock automationDailyField">
                <span>
                  每日仓位%
                  <FieldHint
                    label="每日仓位口径"
                    text="额度 = 模拟盘总权益 × 该百分比，按 UTC+8 自然日累计已提交开仓的名义金额（张数 × 合约面值 × 价格）；同策略多合约共享同一额度，0 表示不限制，平仓不占用额度；权益读不到时直接拦截开仓。"
                  />
                </span>
                <TextInput inputMode="decimal" value={form.dailyPositionPct} onChange={(event) => updateForm("dailyPositionPct", event.target.value)} />
                <div className={`automationEquityHint ${equityHintTone}`} role="status" aria-live="polite">
                  {equityHint ? (
                    <span>{equityHint}</span>
                  ) : (
                    <>
                      <strong>模拟盘权益 {automationEquity?.equity} USDT</strong>
                      {automationEquity?.availEq ? <span>可用 {automationEquity.availEq} USDT</span> : null}
                      {automationEquity?.equityBasis && automationEquity.equityBasis !== "totalEq" ? (
                        <span>基准 {automationEquity.equityBasis}</span>
                      ) : null}
                      {hasEquityPct && automationEquity?.dailyLimit ? (
                        <span>按 {form.dailyPositionPct}% ≈ {automationEquity.dailyLimit} USDT/日</span>
                      ) : (
                        <span>填百分比后显示每日额度</span>
                      )}
                      {hasEquityPct && automationEquity?.dailyUsedAvailable ? (
                        <span>今日已用 {automationEquity.dailyUsed} USDT</span>
                      ) : null}
                      <span className="automationEquityMeta">
                        {automationEquity?.source === "okx" ? "实时快照" : "缓存快照"}
                        {automationEquity?.snapshotTs
                          ? ` · ${new Date(automationEquity.snapshotTs).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`
                          : ""}
                      </span>
                      {automationEquity?.pctInvalid ? <span className="automationEquityWarn">百分比需为 0–100</span> : null}
                      {automationEquity?.warning ? <span className="automationEquityWarn">{automationEquity.warning}</span> : null}
                    </>
                  )}
                  <Button
                    variant="subtle"
                    size="xs"
                    className="automationRefreshLink"
                    type="button"
                    onClick={() => void loadAutomationEquity(true)}
                    disabled={equityLoading}
                    title={automationEquity?.snapshotTs ? `账户快照：${new Date(automationEquity.snapshotTs).toLocaleString("zh-CN")}` : "刷新模拟盘账户金额"}
                  >
                    {equityLoading ? "读取中" : "刷新"}
                  </Button>
                </div>
              </label>
            </div>
            <div className="cleanCreateFooter">
              <div>
                <strong>{saveNotice || decisionTitle}</strong>
                <span>{saveNotice ? saveStateText : decisionMessage}</span>
                {exitsDisabled ? (
                  <span className="automationFooterWarn">
                    只提醒模式：不下单、不自动平仓，止盈止损不生效。
                  </span>
                ) : null}
              </div>
              <div className="cleanActionRow">
                <Button variant="default" className="secondaryButton" type="button" onClick={() => saveStrategy(Boolean(selectedStrategy))} disabled={saving}>
                  {selectedStrategy ? "保存修改" : "保存为暂停"}
                </Button>
                <Button className="primaryButton" type="button" onClick={() => saveStrategy(Boolean(selectedStrategy), true)} disabled={saving}>
                  保存并启动
                </Button>
              </div>
            </div>
          </section>
        </section>
      ) : null}
    </section>
  );
}

function StrategyListPage({
  onBackToAutomation,
  onEditStrategy,
  onCreateStrategy
}: {
  onBackToAutomation: () => void;
  onEditStrategy: (strategyId: number) => void;
  onCreateStrategy: () => void;
}) {
  const [strategies, setStrategies] = React.useState<AutomationStrategy[]>([]);
  const [signals, setSignals] = React.useState<AutomationSignal[]>([]);
  const [automationStatus, setAutomationStatus] = React.useState<AutomationStatus | null>(null);
  const [query, setQuery] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<"all" | "enabled" | "paused" | "archived">("all");
  const [templateFilter, setTemplateFilter] = React.useState<"all" | "llm_direct" | "ma_cross">("all");
  const [executionFilter, setExecutionFilter] = React.useState<"all" | "simulated_auto" | "signal_only">("all");
  const [pageIndex, setPageIndex] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [status, setStatus] = React.useState("加载中");
  const [saving, setSaving] = React.useState(false);
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);

  const loadStrategies = React.useCallback(async () => {
    const [strategyResponse, signalResponse, statusResponse] = await Promise.all([
      fetch(`${API_BASE}/api/automation/strategies?includeArchived=true`),
      fetch(`${API_BASE}/api/automation/signals?limit=300`),
      fetch(`${API_BASE}/api/automation/status`)
    ]);
    if (!strategyResponse.ok || !signalResponse.ok || !statusResponse.ok) {
      setStatus("策略数据加载失败");
      return;
    }
    const strategyPayload = await strategyResponse.json();
    const signalPayload = await signalResponse.json();
    const statusPayload = await statusResponse.json();
    setStrategies(strategyPayload.data ?? []);
    setSignals(signalPayload.data ?? []);
    setAutomationStatus(statusPayload);
    setUpdatedAt(Date.now());
    setStatus("策略数据已更新");
  }, []);

  React.useEffect(() => {
    loadStrategies().catch(() => setStatus("策略数据加载失败"));
  }, [loadStrategies]);

  const latestSignalsByStrategy = React.useMemo(() => {
    return signals.reduce<Record<number, AutomationSignal>>((next, signal) => {
      if (!next[signal.strategy_id] || signal.ts > next[signal.strategy_id].ts) {
        next[signal.strategy_id] = signal;
      }
      return next;
    }, {});
  }, [signals]);

  const visibleStrategies = React.useMemo(() => {
    const keyword = query.trim().toUpperCase();
    return strategies
      .filter((strategy) => {
        if (strategy.archived && statusFilter !== "archived") return false;
        if (statusFilter === "archived" && !strategy.archived) return false;
        if (statusFilter === "enabled" && !strategy.enabled) return false;
        if (statusFilter === "paused" && strategy.enabled) return false;
        if (templateFilter !== "all" && strategy.template !== templateFilter) return false;
        if (executionFilter !== "all" && strategy.execution_mode !== executionFilter) return false;
        if (!keyword) return true;
        return (
          strategy.name.toUpperCase().includes(keyword) ||
          (strategy.instIds?.length ? strategy.instIds : [strategy.inst_id]).some((item) => item.toUpperCase().includes(keyword)) ||
          automationTemplateLabel(strategy.template).toUpperCase().includes(keyword)
        );
      })
      .sort((left, right) => Number(left.archived) - Number(right.archived) || Number(right.enabled) - Number(left.enabled) || (right.updated_at ?? 0) - (left.updated_at ?? 0));
  }, [executionFilter, query, statusFilter, strategies, templateFilter]);

  const pageCount = Math.max(1, Math.ceil(visibleStrategies.length / pageSize));
  const currentPage = Math.min(pageIndex, pageCount);
  const pageStart = (currentPage - 1) * pageSize;
  const pageStrategies = visibleStrategies.slice(pageStart, pageStart + pageSize);

  React.useEffect(() => {
    setPageIndex(1);
  }, [executionFilter, pageSize, query, statusFilter, templateFilter]);

  const toggleStrategy = async (strategy: AutomationStrategy) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/strategies/${strategy.id}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !strategy.enabled })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "策略状态更新失败");
      setStatus(!strategy.enabled ? "策略已启动" : "策略已暂停");
      await loadStrategies();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "策略状态更新失败");
    } finally {
      setSaving(false);
    }
  };

  const runStrategy = async (strategy: AutomationStrategy) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/strategies/${strategy.id}/run`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "策略运行失败");
      setStatus(payload.data ? "策略已运行一次" : "策略没有产生新记录");
      await loadStrategies();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "策略运行失败");
    } finally {
      setSaving(false);
    }
  };

  const archiveStrategy = async (strategy: AutomationStrategy) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/strategies/${strategy.id}/archive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "手动归档" })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "归档失败");
      setStatus("策略已归档");
      await loadStrategies();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "归档失败");
    } finally {
      setSaving(false);
    }
  };

  const restoreStrategy = async (strategy: AutomationStrategy) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/automation/strategies/${strategy.id}/restore`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "恢复失败");
      setStatus("策略已恢复为暂停状态");
      await loadStrategies();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "恢复失败");
    } finally {
      setSaving(false);
    }
  };

  const enabledCount = strategies.filter((strategy) => strategy.enabled && !strategy.archived).length;
  const archivedCount = strategies.filter((strategy) => strategy.archived).length;
  const llmCount = strategies.filter((strategy) => strategy.template === "llm_direct").length;
  const autoCount = strategies.filter((strategy) => strategy.execution_mode === "simulated_auto").length;

  return (
    <section className="strategiesPage">
      <PageHeader eyebrow="策略管理" title="自动交易策略" description={`${status}${updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={
        <div className="workspaceActions">
          <div className="signalLogInlineStats" aria-label="策略状态">
            <Badge className={`signalLogInlineChip ${automationStatus?.running ? "live" : "warning"}`}>
              引擎{automationStatus?.running ? "运行中" : "未运行"}
            </Badge>
            <Badge className="signalLogInlineChip">总数 <strong>{strategies.length}</strong></Badge>
            <Badge className="signalLogInlineChip">启用 <strong>{automationStatus?.enabledCount ?? enabledCount}</strong></Badge>
            <Badge className="signalLogInlineChip">归档 <strong>{automationStatus?.archivedCount ?? archivedCount}</strong></Badge>
            <Badge className="signalLogInlineChip">LLM <strong>{llmCount}</strong></Badge>
            <Badge className="signalLogInlineChip">虚拟盘 <strong>{autoCount}</strong></Badge>
          </div>
          <Button className="primaryButton slim" size="xs" type="button" onClick={onCreateStrategy}>
            新建策略
          </Button>
          <Button variant="default" size="xs" className="secondaryButton slim" type="button" onClick={onBackToAutomation}>
            返回自动交易
          </Button>
        </div>
      } />
      {status === "加载中" ? <DataLoadingState label="正在读取自动交易策略" compact /> : null}

      <section className="signalLogMinimalControls" aria-label="策略筛选">
        <label className="signalLogMinimalSearch">
          <Search size={15} aria-hidden="true" />
          <TextInput
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="策略名 / 合约 / 模板"
            aria-label="搜索策略"
          />
        </label>
        <div className="signalLogMinimalFilter" aria-label="策略状态">
          {[
            { key: "all", label: "全部" },
            { key: "enabled", label: "启用" },
            { key: "paused", label: "暂停" },
            { key: "archived", label: "归档" }
          ].map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={statusFilter === item.key ? "selected" : ""}
              onClick={() => setStatusFilter(item.key as "all" | "enabled" | "paused" | "archived")}
            >
              {item.label}
            </Button>
          ))}
        </div>
        <div className="signalLogMinimalFilter" aria-label="策略模板">
          {[
            { key: "all", label: "全部模板" },
            { key: "llm_direct", label: "LLM" },
            { key: "ma_cross", label: "MA" }
          ].map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={templateFilter === item.key ? "selected" : ""}
              onClick={() => setTemplateFilter(item.key as "all" | "llm_direct" | "ma_cross")}
            >
              {item.label}
            </Button>
          ))}
        </div>
        <div className="signalLogMinimalFilter" aria-label="运行方式">
          {[
            { key: "all", label: "全部方式" },
            { key: "simulated_auto", label: "虚拟盘" },
            { key: "signal_only", label: "只提醒" }
          ].map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={executionFilter === item.key ? "selected" : ""}
              onClick={() => setExecutionFilter(item.key as "all" | "simulated_auto" | "signal_only")}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </section>

      <section className="signalLogMinimalPanel strategyListPanel">
        <div className="signalLogMinimalPanelHeader">
          <div>
            <ClipboardList size={17} aria-hidden="true" />
            <strong>全部策略</strong>
          </div>
          <span>{visibleStrategies.length}/{strategies.length} 条</span>
        </div>
        <div className="signalLogTableWrap">
          <DataTable className="minimalDataTable strategyDataTable">
            <thead>
              <tr>
                <th>策略</th>
                <th>合约 / 周期</th>
                <th>模板</th>
                <th>运行方式</th>
                <th>下单 / 风控</th>
                <th>最近信号</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {pageStrategies.length ? (
                pageStrategies.map((strategy) => {
                  const latestSignal = latestSignalsByStrategy[strategy.id];
                  return (
                    <tr key={strategy.id}>
                      <td>
                        <strong>{strategy.name}</strong>
                        <small>#{strategy.id} · 冷却 {strategy.cooldown_seconds}s · 最后 {formatTime(strategy.last_eval_ts ?? "")}</small>
                      </td>
                      <td>
                        <strong title={(strategy.instIds?.length ? strategy.instIds : [strategy.inst_id]).join("、")}>{strategyInstrumentLabel(strategy)}</strong>
                        <small>{automationBarLabel(strategy.bar)}</small>
                      </td>
                      <td>
                        <strong>{automationTemplateLabel(strategy.template)}</strong>
                        <small>{automationStrategyStyleLabel(strategy)}</small>
                      </td>
                      <td>{automationExecutionModeLabel(strategy.execution_mode)}</td>
                      <td>
                        <strong>{formatValue(strategy.sz)} 张</strong>
                        <small>止盈 {formatValue(strategy.take_profit_pct ?? "0")}% · 止损 {formatValue(strategy.stop_loss_pct ?? "0")}%</small>
                      </td>
                      <td>
                        <Badge className={`signalLogActionTag ${latestSignal ? automationActionClass(latestSignal.action) || "neutral" : "neutral"}`}>
                          {latestSignal ? automationActionLabel(latestSignal.action) : "--"}
                        </Badge>
                      </td>
                      <td>
                        <Badge className={`signalLogDecisionTag ${strategy.archived ? "warning" : strategy.enabled ? "ok" : "warning"}`}>
                          {automationArchiveStateLabel(strategy)}
                        </Badge>
                      </td>
                      <td>
                        <span className="compactRowActions strategyActions">
                          <Button variant="subtle" size="xs" className="signalLogDetailButton" type="button" onClick={() => onEditStrategy(strategy.id)} disabled={saving}>
                            <Pencil size={13} />
                            编辑
                          </Button>
                          <ActionIcon variant="subtle"
                            className="signalLogIconButton"
                            type="button"
                            onClick={() => runStrategy(strategy)}
                            disabled={saving || strategy.archived}
                            title="运行一次"
                            aria-label={`运行 ${strategy.name}`}
                          >
                            <RefreshCw size={16} />
                          </ActionIcon>
                          <ActionIcon variant="subtle"
                            className={`signalLogIconButton strategyToggleButton ${strategy.enabled ? "" : "start"}`}
                            type="button"
                            onClick={() => toggleStrategy(strategy)}
                            disabled={saving || strategy.archived}
                            title={strategy.enabled ? "暂停策略" : "启动策略"}
                            aria-label={`${strategy.enabled ? "暂停" : "启动"} ${strategy.name}`}
                          >
                            {strategy.enabled ? <Pause size={16} /> : <Play size={16} />}
                          </ActionIcon>
                          {strategy.archived ? (
                            <Button variant="subtle" size="xs" className="signalLogDetailButton" type="button" onClick={() => restoreStrategy(strategy)} disabled={saving} title="恢复为暂停">
                              恢复
                            </Button>
                          ) : (
                            <Button variant="subtle" size="xs" className="signalLogDetailButton" type="button" onClick={() => archiveStrategy(strategy)} disabled={saving} title="归档策略">
                              归档
                            </Button>
                          )}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr className="signalLogEmptyRow">
                  <td colSpan={8}>没有符合条件的策略</td>
                </tr>
              )}
            </tbody>
          </DataTable>
        </div>
        <div className="paginationBar">
          <span>
            第 {visibleStrategies.length ? pageStart + 1 : 0}-{Math.min(pageStart + pageSize, visibleStrategies.length)} 条 / 共 {visibleStrategies.length} 条
          </span>
          <label>
            每页
            <Select aria-label="每页策略数" value={String(pageSize)} onChange={(value) => value && setPageSize(Number(value))}
              data={[10, 20, 50].map((size) => ({ value: String(size), label: String(size) }))} size="xs" w={80} />
          </label>
          {pageCount > 1 ? (
            <div className="rowActions">
              <Button variant="default" size="xs" className="rowAction" type="button" onClick={() => setPageIndex(1)} disabled={currentPage <= 1}>
                首页
              </Button>
              <Button variant="default" size="xs" className="rowAction" type="button" onClick={() => setPageIndex((current) => Math.max(1, current - 1))} disabled={currentPage <= 1}>
                上一页
              </Button>
              <span className="pageIndex">{currentPage}/{pageCount}</span>
              <Button variant="default" size="xs"
                className="rowAction"
                type="button"
                onClick={() => setPageIndex((current) => Math.min(pageCount, current + 1))}
                disabled={currentPage >= pageCount}
              >
                下一页
              </Button>
              <Button variant="default" size="xs" className="rowAction" type="button" onClick={() => setPageIndex(pageCount)} disabled={currentPage >= pageCount}>
                末页
              </Button>
            </div>
          ) : (
            <span className="pageIndex">1/1</span>
          )}
        </div>
      </section>
    </section>
  );
}

function SignalLogPage({ onOpenSignalDetail }: { onOpenSignalDetail: (signalId: number) => void }) {
  const [signals, setSignals] = React.useState<AutomationSignal[]>([]);
  const [automationStatus, setAutomationStatus] = React.useState<AutomationStatus | null>(null);
  const [query, setQuery] = React.useState("");
  const [actionFilter, setActionFilter] = React.useState("all");
  const [decisionFilter, setDecisionFilter] = React.useState("all");
  const [status, setStatus] = React.useState("加载中");
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);

  const loadSignalLogs = React.useCallback(async () => {
    const [signalResponse, statusResponse] = await Promise.all([
      fetch(`${API_BASE}/api/automation/signals?limit=300`),
      fetch(`${API_BASE}/api/automation/status`)
    ]);
    if (!signalResponse.ok || !statusResponse.ok) {
      setStatus("信号日志接口异常");
      return;
    }
    const signalPayload = await signalResponse.json();
    const statusPayload = await statusResponse.json();
    setSignals(signalPayload.data ?? []);
    setAutomationStatus(statusPayload);
    setUpdatedAt(Date.now());
    setStatus("信号日志已更新");
  }, []);

  React.useEffect(() => {
    loadSignalLogs().catch(() => setStatus("信号日志加载失败"));
    const timer = window.setInterval(() => {
      if (!document.hidden) loadSignalLogs().catch(() => undefined);
    }, 10000);
    return () => window.clearInterval(timer);
  }, [loadSignalLogs]);

  const signalLogRealtime = useRealtimeFeed({
    topics: ["automation.signal", "automation.status"],
    onSnapshotRequired: () => {
      loadSignalLogs().catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "automation.signal" || payload.type === "automation.status") {
        loadSignalLogs().catch(() => undefined);
        setStatus("信号日志实时事件已同步");
      }
      if (payload.type === "error" || payload.type === "stale") {
        setStatus(payload.message ?? "实时通道暂不可用，已保留 REST 回退");
      }
    }
  });

  const visibleSignals = React.useMemo(() => {
    const keyword = query.trim().toUpperCase();
    return signals
      .filter((item) => actionFilter === "all" || item.action === actionFilter)
      .filter((item) => {
        if (decisionFilter === "all") return true;
        if (decisionFilter === "risk") return ["blocked", "failed", "llm_failed"].includes(item.decision);
        return item.decision === decisionFilter;
      })
      .filter((item) => {
        if (!keyword) return true;
        return [item.inst_id, item.strategy_name, item.action, item.decision, item.reason, item.message]
          .filter(Boolean)
          .some((value) => String(value).toUpperCase().includes(keyword));
      });
  }, [actionFilter, decisionFilter, query, signals]);

  const longCount = signals.filter((item) => item.action === "long").length;
  const shortCount = signals.filter((item) => item.action === "short").length;
  const blockedCount = signals.filter((item) => item.decision === "blocked" || item.decision === "failed" || item.decision === "llm_failed").length;
  const aiAnalysisCount = signals.filter((item) => signalLlmAnalysis(item) || signalLlmFailure(item)).length;
  const resultFilters = [
    { key: "all", label: "全部结果" },
    { key: "submitted", label: "已提交" },
    { key: "risk", label: "拦截失败" },
    { key: "signal_only", label: "仅记录" }
  ];
  const decisionTone = (decision?: string) => {
    if (decision === "submitted") return "ok";
    if (decision === "blocked" || decision === "failed" || decision === "llm_failed") return "blocked";
    if (decision === "signal_only" || decision === "observed") return "note";
    if (decision === "skipped") return "warning";
    return "";
  };

  return (
    <section className="signalsPage">
      <div className="workspaceHeader signalLogMinimalHeader">
        <div>
          <span className="eyebrow">自动交易</span>
          <h1>信号日志</h1>
          <p>{status}{updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}</p>
          {status === "加载中" ? <DataLoadingState label="正在读取信号日志" compact /> : null}
        </div>
        <div className="signalLogInlineStats" aria-label="信号日志状态">
          <Badge className={`signalLogInlineChip ${signalLogRealtime.connected ? "live" : "warning"}`}>
            {signalLogRealtime.connected ? "实时通道" : "REST 回退"}
          </Badge>
          <Badge className={`signalLogInlineChip ${automationStatus?.running ? "live" : "warning"}`}>
            引擎{automationStatus?.running ? "运行中" : "未运行"}
          </Badge>
          <Badge className="signalLogInlineChip">总数 <strong>{signals.length}</strong></Badge>
          <Badge className="signalLogInlineChip">做多 <strong>{longCount}</strong></Badge>
          <Badge className="signalLogInlineChip">做空 <strong>{shortCount}</strong></Badge>
          <Badge className="signalLogInlineChip">风控 <strong>{blockedCount}</strong></Badge>
          <Badge className="signalLogInlineChip">AI <strong>{aiAnalysisCount}</strong></Badge>
        </div>
      </div>

      {automationStatus?.warning ? <Notice tone="warning">{automationStatus.warning}</Notice> : null}

      <section className="signalLogMinimalControls" aria-label="信号筛选">
        <label className="signalLogMinimalSearch">
          <Search size={15} aria-hidden="true" />
          <TextInput
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="合约 / 策略 / 原因"
            aria-label="搜索信号"
          />
        </label>
        <div className="signalLogMinimalFilter" aria-label="信号方向">
          {signalActionFilters.map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={actionFilter === item.key ? "selected" : ""}
              onClick={() => setActionFilter(item.key)}
              title={item.title ?? item.label}
            >
              {item.label}
            </Button>
          ))}
        </div>
        <div className="signalLogMinimalFilter result" aria-label="执行结果">
          {resultFilters.map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={decisionFilter === item.key ? "selected" : ""}
              onClick={() => setDecisionFilter(item.key)}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </section>

      <section className="signalLogMinimalPanel">
        <div className="signalLogMinimalPanelHeader">
          <div>
            <ListChecks size={17} aria-hidden="true" />
            <strong>信号记录</strong>
          </div>
          <span>{visibleSignals.length}/{signals.length} 条</span>
        </div>
        <div className="signalLogTableWrap">
          <DataTable className="signalLogTable">
            <thead>
              <tr>
                <th>时间</th>
                <th>合约 / 策略</th>
                <th>信号</th>
                <th>结果</th>
                <th>原因</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {visibleSignals.length ? (
                visibleSignals.map((signal) => {
                  const reason = signalReason(signal);
                  const signalDate = new Date(Number(signal.ts));
                  const hasValidDate = Number.isFinite(signalDate.getTime());
                  const hasAi = Boolean(signalLlmAnalysis(signal) || signalLlmFailure(signal));
                  return (
                    <SelectableTableRow key={signal.id} onSelect={() => onOpenSignalDetail(signal.id)} title="点击查看信号详情">
                      <td title={formatTime(signal.ts)}>
                        <strong>{formatClockSecond(signal.ts)}</strong>
                        <small>{hasValidDate ? formatDayHint(signal.ts) : formatTime(signal.ts)}</small>
                      </td>
                      <td>
                        <strong>{signal.inst_id}</strong>
                        <small>
                          {signal.strategy_name ?? `策略 #${signal.strategy_id}`}
                          {hasAi ? <Badge className="signalLogAiTag">AI</Badge> : null}
                        </small>
                      </td>
                      <td>
                        <Badge className={`signalLogActionTag ${automationActionClass(signal.action) || "neutral"}`}>
                          {automationActionLabel(signal.action)}
                        </Badge>
                      </td>
                      <td>
                        <Badge className={`signalLogDecisionTag ${decisionTone(signal.decision)}`}>
                          {automationDecisionLabel(signal.decision)}
                        </Badge>
                      </td>
                      <td className="signalLogTableReason">
                        <strong>{reason}</strong>
                        <small>{signal.message || "点击详情查看完整判断依据"}</small>
                      </td>
                      <td>
                        <Button variant="subtle" size="xs"
                          className="signalLogDetailButton"
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            onOpenSignalDetail(signal.id);
                          }}
                        >
                          <BookOpen size={13} aria-hidden="true" />
                          详情
                        </Button>
                      </td>
                    </SelectableTableRow>
                  );
                })
              ) : (
                <tr className="signalLogEmptyRow">
                  <td colSpan={6}>暂无符合条件的信号记录</td>
                </tr>
              )}
            </tbody>
          </DataTable>
        </div>
      </section>
    </section>
  );
}

function SignalDetailPage({ signalId, onBack }: { signalId: number | null; onBack: () => void }) {
  const [signal, setSignal] = React.useState<AutomationSignal | null>(null);
  const [strategies, setStrategies] = React.useState<AutomationStrategy[]>([]);
  const [automationStatus, setAutomationStatus] = React.useState<AutomationStatus | null>(null);
  const [status, setStatus] = React.useState(signalId ? "加载中" : "未选择信号");
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);

  const loadSignalDetail = React.useCallback(async () => {
    if (!signalId) {
      setSignal(null);
      setStatus("未选择信号");
      return;
    }
    const [signalResponse, strategyResponse, statusResponse] = await Promise.all([
      fetch(`${API_BASE}/api/automation/signals/${signalId}`),
      fetch(`${API_BASE}/api/automation/strategies?includeArchived=true`),
      fetch(`${API_BASE}/api/automation/status`)
    ]);
    if (signalResponse.status === 404) {
      setSignal(null);
      setStatus(`信号 #${signalId} 不存在`);
      return;
    }
    if (!signalResponse.ok || !strategyResponse.ok || !statusResponse.ok) {
      setStatus("信号详情接口异常");
      return;
    }
    const signalPayload = await signalResponse.json();
    const strategyPayload = await strategyResponse.json();
    const statusPayload = await statusResponse.json();
    setSignal(signalPayload.data ?? null);
    setStrategies(strategyPayload.data ?? []);
    setAutomationStatus(statusPayload);
    setUpdatedAt(Date.now());
    setStatus("信号详情已更新");
  }, [signalId]);

  React.useEffect(() => {
    loadSignalDetail().catch(() => setStatus("信号详情加载失败"));
  }, [loadSignalDetail]);

  const selectedStrategy = React.useMemo(
    () => strategies.find((item) => item.id === signal?.strategy_id) ?? null,
    [signal, strategies]
  );
  const selectedReason = signal ? signalReason(signal) : "";
  const selectedMa = parseMaSignalReason(selectedReason);
  const selectedRaw = signal ? signalRawPayload(signal) : null;
  const selectedRiskSnapshot = signal ? signalRiskSnapshot(signal) : null;
  const selectedExecutionSteps = signal ? signalExecutionSteps(signal) : [];
  const selectedLlmAnalysis = signal ? signalLlmAnalysis(signal) ?? signalLlmFailure(signal) : null;
  const selectedLlmUsage = signal ? signalLlmUsage(signal) : null;

  return (
    <section className="signalsPage signalDetailPage">
      <PageHeader eyebrow="自动交易" title={signal ? `信号详情 #${signal.id}` : "信号详情"} description={`${status}${updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={
        <div className="workspaceActions">
          <Button variant="default" size="xs" className="secondaryButton slim" type="button" onClick={onBack}>
            <ListChecks size={15} aria-hidden="true" />
            返回信号列表
          </Button>
          <div className="statusPills" aria-label="信号详情状态">
            <Badge className={`statusPill ${automationStatus?.running ? "live" : "warning"}`}>
              引擎{automationStatus?.running ? "运行中" : "未运行"}
            </Badge>
            <Badge className={`statusPill ${automationStatus?.globalStateAvailable === false || automationStatus?.globalPaused || automationStatus?.circuitBreakerActive ? "warning" : "live"}`}>
              {automationGlobalStateLabel(automationStatus)}
            </Badge>
            <Badge className="statusPill">轮询 {automationStatus?.intervalSeconds ?? "--"}秒</Badge>
            <Badge className="statusPill">告警 {automationStatus?.alertCount ?? 0}</Badge>
            <Badge className="statusPill">#{signalId ?? "--"}</Badge>
          </div>
          <IconButton label="刷新信号详情" onClick={() => loadSignalDetail().catch(() => setStatus("信号详情加载失败"))}>
            <RefreshCw size={16} />
          </IconButton>
        </div>
      } />
      {status === "加载中" ? <DataLoadingState label="正在读取信号详情" compact /> : null}

      {automationStatus?.warning ? <Notice tone="warning">{automationStatus.warning}</Notice> : null}

      {signal ? (
        <>
          <section className="signalDetailSummary">
            <Metric label="信号方向" value={automationActionLabel(signal.action)} valueClass={automationActionClass(signal.action)} />
            <Metric label="执行结果" value={automationDecisionLabel(signal.decision)} valueClass={automationDecisionClass(signal.decision)} />
            <Metric label="合约" value={signal.inst_id} />
            <Metric label="策略" value={signal.strategy_name ?? selectedStrategy?.name ?? `#${signal.strategy_id}`} />
            <Metric label="信号时间" value={formatTime(signal.ts)} />
            <Metric label="AI 分析" value={selectedLlmAnalysis ? "已记录" : "无"} valueClass={selectedLlmAnalysis ? "up" : ""} />
          </section>

          <section className="positionsPanel signalDetailFullPanel">
            <PanelHeader icon={<BookOpen size={17} />} title="信号详情" meta={`#${signal.id}`} />
            <div className="signalDetail signalDetailStandalone">
              <div className={`signalDetailHero ${automationActionClass(signal.action)}`}>
                <div className="signalDetailIcon">
                  {signal.action === "long" ? (
                    <TrendingUp size={22} aria-hidden="true" />
                  ) : signal.action === "short" ? (
                    <TrendingDown size={22} aria-hidden="true" />
                  ) : (
                    <Info size={22} aria-hidden="true" />
                  )}
                </div>
                <div>
                  <span>{automationTemplateLabel(signal.template)} · {automationBarLabel(signal.bar)}</span>
                  <h2>{automationActionLabel(signal.action)}</h2>
                  <p>{signal.strategy_name ?? selectedStrategy?.name ?? `策略 #${signal.strategy_id}`}</p>
                </div>
                <Badge className={`statusPill ${automationDecisionClass(signal.decision)}`}>
                  {automationDecisionLabel(signal.decision)}
                </Badge>
              </div>

              <div className="signalDetailMetrics">
                <Metric label="合约" value={signal.inst_id} />
                <Metric label="信号价格" value={formatValue(signal.price)} />
                <Metric label="下单数量" value={signal.sz ? `${formatValue(signal.sz)} 张` : "--"} />
                <Metric label="信号时间" value={formatTime(signal.ts)} />
                <Metric label="K线时间" value={signalCandleTime(signal)} />
                <Metric label="OKX 方向" value={signalOkxOrderText(signal)} />
                <Metric label="执行模式" value={selectedStrategy ? automationExecutionModeLabel(selectedStrategy.execution_mode) : signal.decision} />
              </div>

              <div className="signalReasonBox">
                <strong>为什么{automationActionLabel(signal.action)}</strong>
                <p>{signalWhyText(signal)}</p>
              </div>

              {selectedMa ? (
                <div className="maEvidence">
                  <div className="maEvidenceTitle">
                    <strong>均线交叉依据</strong>
                    <span>MA{selectedMa.fastLabel} / MA{selectedMa.slowLabel}</span>
                  </div>
                  <div className="maEvidenceGrid">
                    <div className="maEvidenceCard">
                      <span>上一根快线</span>
                      <strong>{selectedMa.previousFast}</strong>
                    </div>
                    <div className="maEvidenceCard">
                      <span>上一根慢线</span>
                      <strong>{selectedMa.previousSlow}</strong>
                    </div>
                    <div className={`maEvidenceCard ${automationActionClass(signal.action)}`}>
                      <span>当前快线</span>
                      <strong>{selectedMa.currentFast}</strong>
                    </div>
                    <div className="maEvidenceCard">
                      <span>当前慢线</span>
                      <strong>{selectedMa.currentSlow}</strong>
                    </div>
                  </div>
                  <div className={`signalRuleText ${automationActionClass(signal.action)}`}>
                    {signal.action === "long"
                      ? `判断规则：上一根 MA${selectedMa.fastLabel} 未高于 MA${selectedMa.slowLabel}，当前 MA${selectedMa.fastLabel} 高于 MA${selectedMa.slowLabel}，所以是上穿做多。`
                      : signal.action === "short"
                        ? `判断规则：上一根 MA${selectedMa.fastLabel} 未低于 MA${selectedMa.slowLabel}，当前 MA${selectedMa.fastLabel} 低于 MA${selectedMa.slowLabel}，所以是下穿做空。`
                        : "判断规则：当前没有形成明确上穿或下穿，因此保持观望。"}
                  </div>
                </div>
              ) : null}

              <div className="signalReasonBox muted">
                <strong>执行说明</strong>
                <p>{signal.message || "--"}</p>
              </div>

              <div className="signalReasonBox muted">
                <strong>风控快照</strong>
                {selectedRiskSnapshot ? (
                  <>
                    <p>{selectedRiskSnapshot.message || "--"}</p>
                    <div className="riskSnapshotMeta">
                      <Badge className={`statusPill ${selectedRiskSnapshot.allowed ? "live" : "warning"}`}>
                        {selectedRiskSnapshot.allowed ? "允许" : "拦截"}
                      </Badge>
                      <Badge className="statusPill">{selectedRiskSnapshot.severity}</Badge>
                      <Badge className="statusPill">{selectedRiskSnapshot.checks?.length ?? 0} 项检查</Badge>
                    </div>
                    <div className="riskSnapshotChecks">
                      {(selectedRiskSnapshot.checks ?? []).length ? (
                        (selectedRiskSnapshot.checks ?? []).map((item, index) => {
                          const check = item as Record<string, unknown>;
                          return (
                            <div className="riskSnapshotCheck" key={`${String(check.key ?? index)}-${index}`}>
                              <strong>{String(check.label ?? check.key ?? "检查")}</strong>
                              <span className={riskStatusClass(String(check.status ?? ""))}>{riskStatusLabel(String(check.status ?? ""))}</span>
                              <small>{String(check.message ?? "")}</small>
                              {check.value ? <small className="mutedValue">{String(check.value)}</small> : null}
                            </div>
                          );
                        })
                      ) : (
                        <p>暂无详细检查项。</p>
                      )}
                    </div>
                  </>
                ) : (
                  <p>暂无风控快照。旧信号会直接回退到原始数据与说明文本。</p>
                )}
              </div>

              <div className="signalReasonBox muted">
                <strong>执行步骤</strong>
                {selectedExecutionSteps.length ? (
                  <div className="executionStepList">
                    {selectedExecutionSteps.map((step) => (
                      <div className="executionStepItem" key={step.id}>
                        <div className="executionStepHeader">
                          <strong>{step.action}</strong>
                          <span className={executionStepStatusClass(step.status)}>{executionStepStatusLabel(step.status)}</span>
                        </div>
                        <p>{step.message || "--"}</p>
                        <small>{step.request_json ? String(step.request_json) : "--"}</small>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>暂无执行步骤。旧信号会从原始信号数据中回退读取相关字段。</p>
                )}
              </div>

              {selectedLlmAnalysis ? (
                <div className={`aiAnalysisPanel ${selectedLlmAnalysis.status === "failed" ? "failed" : ""}`}>
                  <div className="aiAnalysisHeader">
                    <div>
                      <BrainCircuit size={18} aria-hidden="true" />
                      <strong>AI 分析</strong>
                    </div>
                    <Badge className={`statusPill ${llmRecommendationClass(selectedLlmAnalysis.recommendation)}`}>
                      {selectedLlmAnalysis.status === "failed"
                        ? "分析失败"
                        : llmRecommendationLabel(selectedLlmAnalysis.recommendation)}
                    </Badge>
                  </div>
                  {selectedLlmAnalysis.status === "failed" ? (
                    <p className="aiSummary">{selectedLlmAnalysis.error || "LLM 分析失败"}</p>
                  ) : (
                    <>
                      <div className="aiAnalysisGrid">
                        <Metric label="模型" value={selectedLlmAnalysis.model || "--"} />
                        <Metric label="模式" value={llmModeLabel(selectedLlmAnalysis.mode)} />
                        <Metric label="置信度" value={`${selectedLlmAnalysis.confidence ?? 0}%`} />
                      </div>
                      <p className="aiSummary">{selectedLlmAnalysis.summary || "--"}</p>
                      <div className="aiListGrid">
                        <div className="aiList">
                          <strong>理由</strong>
                          {(selectedLlmAnalysis.reasons ?? []).length ? (
                            (selectedLlmAnalysis.reasons ?? []).map((item, index) => <span key={`${item}-${index}`}>{item}</span>)
                          ) : (
                            <span>暂无</span>
                          )}
                        </div>
                        <div className="aiList risks">
                          <strong>风险</strong>
                          {(selectedLlmAnalysis.risks ?? []).length ? (
                            (selectedLlmAnalysis.risks ?? []).map((item, index) => <span key={`${item}-${index}`}>{item}</span>)
                          ) : (
                            <span>暂无</span>
                          )}
                        </div>
                      </div>
                      <div className="signalReasonBox muted">
                        <strong>失效条件</strong>
                        <p>{selectedLlmAnalysis.invalidation || "--"}</p>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="signalReasonBox muted">
                  <strong>AI 分析</strong>
                  <p>该信号没有 AI 分析。启用 AI 配置后，新产生的信号会自动记录分析结果。</p>
                </div>
              )}

              {selectedLlmUsage ? (
                <div className="signalReasonBox muted">
                  <strong>本次 AI 用量</strong>
                  <div className="aiAnalysisGrid usageInlineMetrics">
                    <Metric label="总 Token" value={formatTokenCount(Number(selectedLlmUsage.total_tokens ?? 0))} />
                    <Metric label="输入 / 输出" value={`${formatTokenCount(Number(selectedLlmUsage.prompt_tokens ?? 0))} / ${formatTokenCount(Number(selectedLlmUsage.completion_tokens ?? 0))}`} />
                    <Metric label="耗时" value={formatLatency(Number(selectedLlmUsage.duration_ms ?? 0))} />
                    <Metric label="缓存 Token" value={formatTokenCount(Number(selectedLlmUsage.cached_tokens ?? 0))} />
                    <Metric label="推理 Token" value={formatTokenCount(Number(selectedLlmUsage.reasoning_tokens ?? 0))} />
                    <Metric label="请求 ID" value={compactRequestId(selectedLlmUsage.request_id)} />
                  </div>
                </div>
              ) : null}

              {selectedRaw ? (
                <div className="rawSignalBlock">
                  <strong>原始信号数据</strong>
                  <pre>{JSON.stringify(selectedRaw, null, 2)}</pre>
                </div>
              ) : null}
            </div>
          </section>
        </>
      ) : (
        <section className="positionsPanel signalDetailEmptyPanel">
          <PanelHeader icon={<BookOpen size={17} />} title="信号详情" meta={signalId ? `#${signalId}` : "--"} />
          <EmptyState>请选择一条信号查看详情，或返回信号列表重新打开。</EmptyState>
        </section>
      )}
    </section>
  );
}

function LlmUsagePage() {
  const [usagePayload, setUsagePayload] = React.useState<LlmUsageResponse | null>(null);
  const [requestFilter, setRequestFilter] = React.useState("all");
  const [usageStatusFilter, setUsageStatusFilter] = React.useState("all");
  const [pageIndex, setPageIndex] = React.useState(1);
  const [selectedUsageId, setSelectedUsageId] = React.useState<number | null>(null);
  const [status, setStatus] = React.useState("加载中");
  const [updatedAt, setUpdatedAt] = React.useState<number | null>(null);
  const pageSize = 20;

  const loadUsage = React.useCallback(async () => {
    const params = new URLSearchParams({
      limit: String(pageSize),
      offset: String((pageIndex - 1) * pageSize)
    });
    if (requestFilter !== "all") params.set("requestType", requestFilter);
    if (usageStatusFilter !== "all") params.set("status", usageStatusFilter);
    const response = await fetch(`${API_BASE}/api/llm/usage?${params.toString()}`);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      setStatus(payload.detail ?? "AI 用量加载失败");
      return;
    }
    setUsagePayload(payload as LlmUsageResponse);
    setUpdatedAt(Date.now());
    setStatus("AI 用量已更新");
  }, [pageIndex, requestFilter, usageStatusFilter]);

  React.useEffect(() => {
    loadUsage().catch(() => setStatus("AI 用量加载失败"));
  }, [loadUsage]);

  React.useEffect(() => {
    setPageIndex(1);
  }, [requestFilter, usageStatusFilter]);

  const logs = usagePayload?.data ?? [];
  const summary = usagePayload?.summary ?? {
    calls: 0,
    promptTokens: 0,
    completionTokens: 0,
    totalTokens: 0,
    cachedTokens: 0,
    reasoningTokens: 0,
    cacheHitTokens: 0,
    cacheMissTokens: 0,
    failedCalls: 0,
    avgDurationMs: 0
  };
  const last24h = usagePayload?.last24h ?? summary;
  const paging = usagePayload?.paging ?? {
    limit: pageSize,
    offset: 0,
    hasMore: false,
    total: 0,
    page: pageIndex,
    pageCount: 1
  };
  const selectedLog = React.useMemo(
    () => logs.find((item) => item.id === selectedUsageId) ?? null,
    [logs, selectedUsageId]
  );
  const rawUsage = selectedLog ? parseRawUsage(selectedLog.raw_usage_json) : null;
  const failedRate = summary.calls ? `${((summary.failedCalls / summary.calls) * 100).toLocaleString("zh-CN", { maximumFractionDigits: 1 })}%` : "0%";

  return (
    <section className="usagePage">
      <PageHeader eyebrow="AI 用量" title="LLM Token 用量" description={`${status}${updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={
        <div className="signalLogInlineStats" aria-label="AI 用量状态">
          <Badge className="signalLogInlineChip live">总调用 <strong>{formatTokenCount(summary.calls)}</strong></Badge>
          <Badge className="signalLogInlineChip">总 Token <strong>{formatTokenCount(summary.totalTokens)}</strong></Badge>
          <Badge className="signalLogInlineChip">24h <strong>{formatTokenCount(last24h.totalTokens)}</strong></Badge>
          <Badge className={`signalLogInlineChip ${summary.failedCalls ? "warning" : "live"}`}>失败率 <strong>{failedRate}</strong></Badge>
          <Badge className="signalLogInlineChip">平均 <strong>{formatLatency(summary.avgDurationMs)}</strong></Badge>
        </div>
      } />
      {status === "加载中" ? <DataLoadingState label="正在读取 AI 用量记录" compact /> : null}

      <section className="signalLogMinimalControls usageMinimalControls" aria-label="AI 用量筛选">
        <div className="signalLogMinimalFilter" aria-label="调用类型">
          {llmUsageRequestFilters.map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={requestFilter === item.key ? "selected" : ""}
              onClick={() => setRequestFilter(item.key)}
              title={item.title ?? item.label}
            >
              {item.label}
            </Button>
          ))}
        </div>
        <div className="signalLogMinimalFilter" aria-label="调用状态">
          {llmUsageStatusFilters.map((item) => (
            <Button variant="subtle" size="xs"
              key={item.key}
              type="button"
              className={usageStatusFilter === item.key ? "selected" : ""}
              onClick={() => setUsageStatusFilter(item.key)}
              title={item.title ?? item.label}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </section>

      <section className="signalLogMinimalPanel usageListPanel">
        <div className="signalLogMinimalPanelHeader">
          <div>
            <BarChart3 size={17} aria-hidden="true" />
            <strong>Token 明细</strong>
          </div>
          <span>{formatTokenCount(logs.length)}/{formatTokenCount(paging.total ?? logs.length)} 条</span>
        </div>
        <div className="signalLogTableWrap">
          <DataTable className="minimalDataTable usageDataTable">
            <thead>
              <tr>
                <th>时间 / 类型</th>
                <th>模型</th>
                <th>合约 / 周期</th>
                <th>Token</th>
                <th>耗时</th>
                <th>状态</th>
                <th>请求</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {logs.length ? (
                logs.map((log) => {
                  const expanded = selectedLog?.id === log.id;
                  const rowRawUsage = expanded ? rawUsage : null;
                  return (
                    <React.Fragment key={log.id}>
                      <SelectableTableRow onSelect={() => setSelectedUsageId(expanded ? null : log.id)} selected={expanded} title={log.error || log.request_id}>
                        <td>
                          <strong>{formatTime(log.ts)}</strong>
                          <small>{llmUsageRequestTypeLabel(log.request_type)}</small>
                        </td>
                        <td>
                          <strong>{log.model || "--"}</strong>
                          <small>{compactRequestId(log.request_id)}</small>
                        </td>
                        <td>
                          <strong>{log.inst_id || "--"}</strong>
                          <small>{log.bar || "--"} · {log.strategy_id ? `策略 #${log.strategy_id}` : "无策略"}</small>
                        </td>
                        <td>
                          <strong>{formatTokenCount(log.total_tokens)}</strong>
                          <small>入 {formatTokenCount(log.prompt_tokens)} / 出 {formatTokenCount(log.completion_tokens)}</small>
                        </td>
                        <td>{formatLatency(log.duration_ms)}</td>
                        <td>
                          <Badge className={`signalLogDecisionTag ${llmUsageStatusClass(log.status) === "down" ? "blocked" : llmUsageStatusClass(log.status) === "up" ? "ok" : "warning"}`}>
                            {llmUsageStatusLabel(log.status)}
                          </Badge>
                        </td>
                        <td>
                          <strong>{log.finish_reason || "--"}</strong>
                          <small>{log.error || "调用完成"}</small>
                        </td>
                        <td>
                          <Button variant="subtle" size="xs"
                            className="signalLogDetailButton"
                            type="button"
                            onClick={(event) => {
                              event.stopPropagation();
                              setSelectedUsageId(expanded ? null : log.id);
                            }}
                          >
                            <BookOpen size={13} aria-hidden="true" />
                            {expanded ? "收起" : "详情"}
                          </Button>
                        </td>
                      </SelectableTableRow>
                      {expanded ? (
                        <tr className="usageExpandedRow">
                          <td colSpan={8}>
                            <div className="inlineDetailPanel">
                              <div className="inlineDetailMetrics">
                                <Metric label="缓存 Token" value={formatTokenCount(log.cached_tokens)} />
                                <Metric label="推理 Token" value={formatTokenCount(log.reasoning_tokens)} />
                                <Metric label="缓存命中" value={formatTokenCount(log.cache_hit_tokens)} />
                                <Metric label="缓存未命中" value={formatTokenCount(log.cache_miss_tokens)} />
                                <Metric label="请求 ID" value={compactRequestId(log.request_id)} />
                                <Metric label="Finish" value={log.finish_reason || "--"} />
                              </div>
                              {log.error ? (
                                <div className="inlineDetailText">
                                  <strong>错误信息</strong>
                                  <p>{log.error}</p>
                                </div>
                              ) : null}
                              <div className="rawSignalBlock usageRawBlock">
                                <strong>原始 usage</strong>
                                <pre>{JSON.stringify(rowRawUsage ?? {}, null, 2)}</pre>
                              </div>
                            </div>
                          </td>
                        </tr>
                      ) : null}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr className="signalLogEmptyRow">
                  <td colSpan={8}>暂无符合条件的 LLM 调用记录</td>
                </tr>
              )}
            </tbody>
          </DataTable>
        </div>
        <div className="paginationBar">
          <span>第 {paging.page ?? pageIndex} / {paging.pageCount ?? 1} 页 · 共 {formatTokenCount(paging.total ?? logs.length)} 条</span>
          <div className="rowActions">
            <Button variant="default" size="xs" className="rowAction" type="button" onClick={() => setPageIndex(1)} disabled={pageIndex <= 1}>
              首页
            </Button>
            <Button variant="default" size="xs" className="rowAction" type="button" onClick={() => setPageIndex((value) => Math.max(1, value - 1))} disabled={pageIndex <= 1}>
              上一页
            </Button>
            <Button variant="default" size="xs"
              className="rowAction"
              type="button"
              onClick={() => setPageIndex((value) => Math.min(paging.pageCount ?? value + 1, value + 1))}
              disabled={pageIndex >= (paging.pageCount ?? 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      </section>
    </section>
  );
}

function SegmentedField({
  label,
  value,
  options,
  onChange,
  tone = ""
}: {
  label: string;
  value: string;
  options: SegmentedOption[];
  onChange: (value: string) => void;
  tone?: string;
}) {
  return (
    <div className="fieldBlock">
      <Text component="span" size="sm">{label}</Text>
      <SegmentedControl
        className={`segmentedButtons ${tone}`}
        aria-label={label}
        value={value}
        onChange={onChange}
        data={options.map((item) => ({
          value: item.key,
          label: <span title={item.title ?? item.label}>{item.icon ? <span className="segmentedIcon">{item.icon}</span> : null}<span className="segmentedLabel">{item.label}</span></span>
        }))}
        fullWidth
        size="xs"
      />
    </div>
  );
}

function EmptyState({ compact = false, className = "", children }: { compact?: boolean; className?: string; children: React.ReactNode }) {
  return <Paper className={`emptyRow ${compact ? "compact" : ""} ${className}`.trim()} withBorder={compact} shadow="none" role="status">{children}</Paper>;
}

function Notice({ tone = "warning", children }: { tone?: NoticeTone; children: React.ReactNode }) {
  const icon =
    tone === "danger" ? (
      <AlertTriangle size={16} aria-hidden="true" />
    ) : tone === "info" ? (
      <Info size={16} aria-hidden="true" />
    ) : (
      <ShieldAlert size={16} aria-hidden="true" />
    );
  return (
    <Alert
      className={`notice ${tone}`}
      variant="light"
      color={tone === "danger" ? "red" : tone === "info" ? "workspace" : "yellow"}
      icon={icon}
      role={tone === "danger" ? "alert" : "status"}
    >
      {children}
    </Alert>
  );
}

function DataLoadingState({ label, compact = false }: { label: string; compact?: boolean }) {
  return (
    <Group className={`dataLoadingState ${compact ? "compact" : ""}`} gap="xs" role="status" aria-live="polite">
      <Loader size="xs" aria-hidden="true" />
      <Text size="sm">{label}</Text>
    </Group>
  );
}

function DataLoadingSkeleton({ label, variant = "list" }: { label: string; variant?: "rail" | "list" | "metrics" | "radar-list" | "radar-detail" }) {
  const lines = variant === "rail" ? 4 : variant === "metrics" ? 6 : variant === "radar-list" ? 6 : variant === "radar-detail" ? 6 : 3;
  return (
    <Stack className={`dataLoadingSkeleton ${variant}`} gap="xs" aria-label={label} role="status">
      <Text className="srOnly">{label}</Text>
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton className="dataLoadingSkeletonLine" key={index} height={variant === "metrics" ? 36 : 18} aria-hidden="true" />
      ))}
    </Stack>
  );
}

function EarnPage() {
  const [offers, setOffers] = React.useState<EarnListResponse<EarnProduct> | null>(null);
  const [activeOrders, setActiveOrders] = React.useState<EarnListResponse<EarnOrder> | null>(null);
  const [history, setHistory] = React.useState<EarnListResponse<EarnOrder> | null>(null);
  const [eth, setEth] = React.useState<EarnStakingResponse | null>(null);
  const [sol, setSol] = React.useState<EarnStakingResponse | null>(null);
  const [status, setStatus] = React.useState("加载中");
  const [loadError, setLoadError] = React.useState("");
  const [earnUpdatedAt, setEarnUpdatedAt] = React.useState<number | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);
  const [currencyFilter, setCurrencyFilter] = React.useState("");
  const [protocolTypeFilter, setProtocolTypeFilter] = React.useState("");
  const [orderStateFilter, setOrderStateFilter] = React.useState("");
  const [historyAfter, setHistoryAfter] = React.useState("");
  const hasEarnSnapshotRef = React.useRef(false);
  const protocolTypeOptions = [
    { key: "", label: "全部协议" },
    { key: "defi", label: "DeFi" },
    { key: "staking", label: "Staking" }
  ];
  const activeOrderStateOptions = [
    { key: "", label: "全部" },
    { key: "1", label: "收益中" },
    { key: "2", label: "赎回中" },
    { key: "9", label: "上链中" },
    { key: "8", label: "待上车" }
  ];

  const loadEarn = React.useCallback(async (force = false) => {
    setRefreshing(true);
    const hadSnapshot = hasEarnSnapshotRef.current;
    const ccy = currencyFilter.trim().toUpperCase();
    const offerParams = new URLSearchParams();
    const activeParams = new URLSearchParams();
    const historyParams = new URLSearchParams({ limit: "50" });
    const stakingParams = new URLSearchParams({ days: "30", limit: "20" });
    if (ccy) {
      offerParams.set("ccy", ccy);
      activeParams.set("ccy", ccy);
      historyParams.set("ccy", ccy);
    }
    if (protocolTypeFilter) {
      offerParams.set("protocolType", protocolTypeFilter);
      activeParams.set("protocolType", protocolTypeFilter);
      historyParams.set("protocolType", protocolTypeFilter);
    }
    if (orderStateFilter) activeParams.set("state", orderStateFilter);
    if (historyAfter) historyParams.set("after", historyAfter);
    if (force) {
      offerParams.set("force", "true");
      activeParams.set("force", "true");
      historyParams.set("force", "true");
      stakingParams.set("force", "true");
    }

    const readEarnEndpoint = async (url: string) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error("链上赚币接口暂不可用");
      return response.json();
    };
    const requests = await Promise.allSettled([
      readEarnEndpoint(`${API_BASE}/api/earn/offers?${offerParams.toString()}`),
      readEarnEndpoint(`${API_BASE}/api/earn/orders/active?${activeParams.toString()}`),
      readEarnEndpoint(`${API_BASE}/api/earn/orders/history?${historyParams.toString()}`),
      readEarnEndpoint(`${API_BASE}/api/earn/eth?${stakingParams.toString()}`),
      readEarnEndpoint(`${API_BASE}/api/earn/sol?${stakingParams.toString()}`)
    ]);
    const [offerResult, activeResult, historyResult, ethResult, solResult] = requests;
    if (offerResult.status === "fulfilled") setOffers(offerResult.value);
    if (activeResult.status === "fulfilled") setActiveOrders(activeResult.value);
    if (historyResult.status === "fulfilled") setHistory(historyResult.value);
    if (ethResult.status === "fulfilled") setEth(ethResult.value);
    if (solResult.status === "fulfilled") setSol(solResult.value);
    const failed = requests.filter((item) => item.status === "rejected").length;
    if (failed < requests.length) {
      hasEarnSnapshotRef.current = true;
      setEarnUpdatedAt(Date.now());
    }
    setStatus(failed === requests.length ? hadSnapshot ? "更新失败，已保留现有内容" : "链上赚币数据暂不可用" : failed ? "部分数据更新失败，已保留可用内容" : "链上赚币数据已更新");
    setLoadError(failed ? `${failed} 项链上赚币数据暂不可用${hadSnapshot ? "，已保留现有内容" : ""}，请稍后刷新。` : "");
    setRefreshing(false);
  }, [currencyFilter, historyAfter, orderStateFilter, protocolTypeFilter]);

  React.useEffect(() => {
    loadEarn().catch(() => {
      setStatus("链上赚币数据加载失败");
      setRefreshing(false);
    });
  }, [loadEarn]);

  const warnings = [
    ...(offers?.warnings ?? []),
    ...(activeOrders?.warnings ?? []),
    ...(history?.warnings ?? []),
    ...(eth?.warnings ?? []),
    ...(sol?.warnings ?? [])
  ].filter(Boolean);
  const activeData = activeOrders?.data ?? [];
  const historyData = history?.data ?? [];
  const offerData = offers?.data ?? [];
  const ethBalance = eth?.balances?.[0];
  const solBalance = sol?.balances?.[0];
  const activeEarningOrders = activeData.filter((item) => item.state === "1").length;
  const redeemingOrders = activeData.filter((item) => item.state === "2").length;
  const latestHistoryCursor = historyData[historyData.length - 1]?.ordId ?? "";
  const earnInitialLoading = refreshing && !offers && !activeOrders && !history && !eth && !sol;

  return (
    <section className="earnPage">
      <PageHeader eyebrow="链上赚币" title="OKX On-chain Earn" description={`${status}${earnUpdatedAt ? ` · ${new Date(earnUpdatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={<div className="signalLogInlineStats" aria-label="链上赚币连接状态">
          <Badge className={`signalLogInlineChip ${warnings.length || loadError ? "warning" : "live"}`}>{refreshing ? "刷新中" : "只读看板"}</Badge>
          <Badge className="signalLogInlineChip">项目 <strong>{offerData.length}</strong></Badge>
          <Badge className="signalLogInlineChip">活跃订单 <strong>{activeData.length}</strong></Badge>
          <Badge className="signalLogInlineChip">收益中 <strong>{activeEarningOrders}</strong></Badge>
          <Badge className="signalLogInlineChip">赎回中 <strong>{redeemingOrders}</strong></Badge>
        </div>} />

      <Notice tone="info">链上赚币第一版仅展示 OKX 金融产品、订单、质押余额和历史年化数据，不提交申购、赎回或撤销请求。</Notice>
      {loadError ? <Notice tone="warning">{loadError}</Notice> : null}
      {warnings.slice(0, 3).map((warning) => <Notice key={warning}>{warning}</Notice>)}
      {earnInitialLoading ? <DataLoadingSkeleton label="正在读取链上赚币产品、订单与质押数据" /> : null}
      {refreshing && !earnInitialLoading ? <DataLoadingState label="链上赚币数据更新中，已保留当前内容" compact /> : null}

      <section className="signalLogMinimalControls earnControls" aria-label="链上赚币筛选">
        <TextInput className="signalLogMinimalSearch" value={currencyFilter} onChange={(event) => { setHistoryAfter(""); setCurrencyFilter(event.target.value.toUpperCase()); }} placeholder="USDT / ETH / SOL" aria-label="搜索链上赚币币种" leftSection={<Search size={15} aria-hidden="true" />} size="xs" />
        <SegmentedControl className="signalLogMinimalFilter" aria-label="协议类型" value={protocolTypeFilter} onChange={(value) => { setHistoryAfter(""); setProtocolTypeFilter(value); }} data={protocolTypeOptions.map((item) => ({ value: item.key, label: item.label }))} size="xs" />
        <SegmentedControl className="signalLogMinimalFilter" aria-label="活跃订单状态" value={orderStateFilter} onChange={setOrderStateFilter} data={activeOrderStateOptions.map((item) => ({ value: item.key, label: item.label }))} size="xs" />
        <IconButton label="刷新链上赚币" onClick={() => loadEarn(true).catch(() => setStatus("链上赚币数据加载失败"))}>
          <RefreshCw size={16} />
        </IconButton>
      </section>

      <section className="earnSummary">
        <Metric label="Offers 来源" value={offers?.source ?? "--"} />
        <Metric label="订单来源" value={activeOrders?.source ?? "--"} />
        <Metric label="ETH 年化" value={formatEarnRate(eth?.productInfo?.rate)} />
        <Metric label="BETH 数量" value={formatValue(ethBalance?.amt)} />
        <Metric label="SOL 年化" value={formatEarnRate(sol?.productInfo?.rate)} />
        <Metric label="OKSOL 数量" value={formatValue(solBalance?.amt)} />
      </section>

      <section className="earnGrid">
        <Paper component="section" className="positionsPanel earnProductsPanel" p={0}>
          <PanelHeader icon={<Database size={17} />} title="链上赚币项目" meta={`${offerData.length} 项`} />
          <div className="signalLogTableWrap">
            <DataTable className="minimalDataTable earnProductTable">
              <thead>
                <tr>
                  <th>项目</th>
                  <th>预估年化</th>
                  <th>期限 / 状态</th>
                  <th>可投范围</th>
                  <th>赎回期</th>
                  <th>快速赎回限额</th>
                </tr>
              </thead>
              <tbody>
                {offers?.configured === false ? (
                  <tr className="signalLogEmptyRow"><td colSpan={6}>{offers.message ?? "当前环境未配置 OKX API Key"}</td></tr>
                ) : !offers && loadError ? (
                  <tr className="signalLogEmptyRow"><td colSpan={6}>链上赚币项目暂不可用</td></tr>
                ) : offerData.length ? (
                  offerData.map((item) => (
                    <tr key={`${item.productId}-${item.ccy}-${item.term}`}>
                      <td>
                        <strong>{item.ccy} · {item.protocol || item.productId}</strong>
                        <small>{item.protocolType} · ID {item.productId}</small>
                      </td>
                      <td>{formatEarnRate(item.apy)}</td>
                      <td>
                        <strong>{earnTermLabel(item.term)}</strong>
                        <small className={earnStateClass(item.state)}>{item.stateLabel}</small>
                      </td>
                      <td>{earnInvestRangeText(item.investData)}</td>
                      <td>{earnRedeemPeriodLabel(item.redeemPeriod)}</td>
                      <td>{formatValue(item.fastRedemptionDailyLimit)}</td>
                    </tr>
                  ))
                ) : (
                  <tr className="signalLogEmptyRow"><td colSpan={6}>暂无符合条件的链上赚币项目</td></tr>
                )}
              </tbody>
            </DataTable>
          </div>
        </Paper>

        <Paper component="section" className="positionsPanel earnOrdersPanel" p={0}>
          <PanelHeader icon={<WalletCards size={17} />} title="活跃订单" meta={`${activeData.length} 条`} />
          <div className="signalLogTableWrap">
            <DataTable className="minimalDataTable earnOrderTable">
              <thead>
                <tr>
                  <th>订单</th>
                  <th>状态</th>
                  <th>投入</th>
                  <th>收益</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {activeOrders?.configured === false ? (
                  <tr className="signalLogEmptyRow"><td colSpan={5}>{activeOrders.message ?? "当前环境未配置 OKX API Key"}</td></tr>
                ) : !activeOrders && loadError ? (
                  <tr className="signalLogEmptyRow"><td colSpan={5}>活跃订单暂不可用</td></tr>
                ) : activeData.length ? (
                  activeData.map((item) => (
                    <tr key={item.ordId}>
                      <td>
                        <strong>{item.ccy} · {item.protocol || item.productId}</strong>
                        <small>ID {item.ordId} · 产品 {item.productId}</small>
                      </td>
                      <td><Badge className={`signalLogActionTag ${earnStateClass(item.state)}`}>{item.stateLabel}</Badge></td>
                      <td>{earnAmountText(item.investData, ["amt"])}</td>
                      <td>{earnEarningsText(item.earningData)}</td>
                      <td>
                        <strong>{formatTime(item.purchasedTime)}</strong>
                        <small>预计到账 {formatTime(item.estSettlementTime)}</small>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr className="signalLogEmptyRow"><td colSpan={5}>暂无活跃链上赚币订单</td></tr>
                )}
              </tbody>
            </DataTable>
          </div>
        </Paper>

        <EarnStakingPanel data={eth} asset="ETH" unavailable={Boolean(!eth && loadError)} />
        <EarnStakingPanel data={sol} asset="SOL" unavailable={Boolean(!sol && loadError)} />

        <Paper component="section" className="positionsPanel earnHistoryPanel" p={0}>
          <PanelHeader
            icon={<BookOpen size={17} />}
            title="历史订单"
            meta={historyAfter ? "历史分页" : "最新记录"}
            action={
              <div className="earnPanelActions">
                <Button variant="subtle" size="xs" className="rowAction" type="button" disabled={!historyAfter} onClick={() => setHistoryAfter("")}>最新</Button>
                <Button variant="subtle" size="xs" className="rowAction" type="button" disabled={!latestHistoryCursor} onClick={() => setHistoryAfter(latestHistoryCursor)}>更早</Button>
              </div>
            }
          />
          <div className="signalLogTableWrap">
            <DataTable className="minimalDataTable earnHistoryTable">
              <thead>
                <tr>
                  <th>订单</th>
                  <th>状态</th>
                  <th>投入</th>
                  <th>收益</th>
                  <th>创建 / 赎回</th>
                </tr>
              </thead>
              <tbody>
                {history?.configured === false ? (
                  <tr className="signalLogEmptyRow"><td colSpan={5}>{history.message ?? "当前环境未配置 OKX API Key"}</td></tr>
                ) : !history && loadError ? (
                  <tr className="signalLogEmptyRow"><td colSpan={5}>历史订单暂不可用</td></tr>
                ) : historyData.length ? (
                  historyData.map((item) => (
                    <tr key={item.ordId}>
                      <td>
                        <strong>{item.ccy} · {item.protocol || item.productId}</strong>
                        <small>ID {item.ordId} · 产品 {item.productId}</small>
                      </td>
                      <td><Badge className={`signalLogActionTag ${earnStateClass(item.state)}`}>{item.stateLabel}</Badge></td>
                      <td>{earnAmountText(item.investData, ["amt"])}</td>
                      <td>{earnEarningsText(item.earningData)}</td>
                      <td>
                        <strong>{formatTime(item.purchasedTime)}</strong>
                        <small>赎回 {formatTime(item.redeemedTime)}</small>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr className="signalLogEmptyRow"><td colSpan={5}>暂无链上赚币历史订单</td></tr>
                )}
              </tbody>
            </DataTable>
          </div>
        </Paper>
      </section>
    </section>
  );
}

function EarnStakingPanel({ data, asset, unavailable = false }: { data: EarnStakingResponse | null; asset: "ETH" | "SOL"; unavailable?: boolean }) {
  const receiptCcy = data?.receiptCcy ?? (asset === "ETH" ? "BETH" : "OKSOL");
  const balance = data?.balances?.[0];
  const apyPoints = data?.apyPoints ?? [];
  const latestApy = apyPoints[apyPoints.length - 1];
  return (
    <Paper component="section" className="positionsPanel earnStakingPanel" p={0}>
      <PanelHeader icon={<TrendingUp size={17} />} title={`${asset} 质押`} meta={receiptCcy} />
      <div className="earnStakingMetrics">
        <MiniMetric label="当前年化" value={formatEarnRate(data?.productInfo?.rate ?? latestApy?.rate)} />
        <MiniMetric label="最低数量" value={formatValue(data?.productInfo?.minAmt)} />
        <MiniMetric label="赎回天数" value={data?.productInfo?.redemptDays ? `${data.productInfo.redemptDays} 天` : "--"} />
        <MiniMetric label="快速限额" value={formatValue(data?.productInfo?.fastRedemptionDailyLimit)} />
        <MiniMetric label={`${receiptCcy} 数量`} value={formatValue(balance?.amt)} />
        <MiniMetric label="累计收益" value={formatValue(balance?.totalInterestAccrual)} />
      </div>
      {data?.configured === false ? <EmptyState compact>{data.warnings?.[0] ?? "当前环境未配置 OKX API Key，余额和记录不可用。"}</EmptyState> : null}
      <div className="earnApyStrip" aria-label={`${asset} APY 历史`}>
        {apyPoints.slice(-8).map((point) => (
          <div key={`${asset}-${point.ts}`} className="earnApyPoint">
            <span>{new Date(point.ts).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" })}</span>
            <strong>{formatEarnRate(point.rate)}</strong>
          </div>
        ))}
        {unavailable ? <EmptyState compact>质押年化数据暂不可用</EmptyState> : data && apyPoints.length === 0 ? <EmptyState compact>暂无历史年化数据</EmptyState> : null}
      </div>
      <div className="signalLogTableWrap compact">
        <DataTable className="minimalDataTable earnStakingHistoryTable">
          <thead>
            <tr>
              <th>类型</th>
              <th>数量</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {data?.history?.length ? (
              data.history.slice(0, 6).map((item, index) => (
                <tr key={`${asset}-${item.requestTime}-${index}`}>
                  <td>{stakingHistoryTypeLabel(item.type)}</td>
                  <td>{formatValue(item.amt || item.redeemingAmt)}</td>
                  <td><Badge className={`signalLogActionTag ${earnStateClass(item.status)}`}>{item.statusLabel ?? item.status ?? "--"}</Badge></td>
                  <td>{formatTime(item.requestTime)}</td>
                </tr>
              ))
            ) : (
              <tr className="signalLogEmptyRow"><td colSpan={4}>{unavailable ? "质押记录暂不可用" : data?.configured === false ? "配置 API Key 后可查看余额和申购赎回记录" : "暂无质押记录"}</td></tr>
            )}
          </tbody>
        </DataTable>
      </div>
    </Paper>
  );
}

function PositionsPage() {
  const confirmAction = useConfirmAction();
  const [account, setAccount] = React.useState<AccountResponse | null>(null);
  const [settings, setSettings] = React.useState<SettingsStatus | null>(null);
  const [status, setStatus] = React.useState("加载中");
  const [accountUpdatedAt, setAccountUpdatedAt] = React.useState<number | null>(null);
  const [accountRefreshing, setAccountRefreshing] = React.useState(false);
  const [positionSearch, setPositionSearch] = React.useState("");
  const [sideFilter, setSideFilter] = React.useState<PositionSideFilter>("all");
  const [onlyOpen, setOnlyOpen] = React.useState(true);
  const [closeWarning, setCloseWarning] = React.useState("");
  const [closingPositionKey, setClosingPositionKey] = React.useState("");
  const [positionCloseModes, setPositionCloseModes] = React.useState<Record<string, PositionCloseMode>>({});
  const [positionCloseSizes, setPositionCloseSizes] = React.useState<Record<string, string>>({});
  const [positionClosePrices, setPositionClosePrices] = React.useState<Record<string, string>>({});
  const [activeCloseRow, setActiveCloseRow] = React.useState("");
  const accountLoadingRef = React.useRef(false);
  const accountInitialLoading = accountRefreshing && !account;

  const loadAccount = React.useCallback(async (force = false) => {
    if (accountLoadingRef.current) return;
    accountLoadingRef.current = true;
    setAccountRefreshing(true);
    try {
      const response = await fetch(`${API_BASE}/api/account${force ? "?force=true" : ""}`);
      if (!response.ok) {
        setAccount((current) => accountFailureSnapshot(current, "持仓数据"));
        setStatus("持仓接口异常");
        return;
      }
      const payload = await response.json();
      setAccount(payload);
      setAccountUpdatedAt(Date.now());
      if (!payload.configured) {
        setStatus("未配置 API Key");
      } else if (payload.warning) {
        setStatus("连接波动，已显示可用缓存");
      } else {
        setStatus(payload.source === "okx" ? "持仓信息已实时更新" : "持仓信息已加载");
      }
    } catch {
      setAccount((current) => accountFailureSnapshot(current, "持仓数据"));
      setStatus("持仓接口异常");
    } finally {
      accountLoadingRef.current = false;
      setAccountRefreshing(false);
    }
  }, []);

  const loadSettings = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/settings/status`);
    if (!response.ok) return;
    setSettings(await response.json());
  }, []);

  React.useEffect(() => {
    loadAccount().catch(() => setStatus("持仓信息加载失败"));
    loadSettings().catch(() => undefined);
    const refreshVisiblePositions = () => {
      if (!document.hidden) {
        loadAccount().catch(() => undefined);
      }
    };
    const timer = window.setInterval(refreshVisiblePositions, ACCOUNT_POLL_MS);
    document.addEventListener("visibilitychange", refreshVisiblePositions);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshVisiblePositions);
    };
  }, [loadAccount, loadSettings]);

  const activeEnvironment = account?.environment ?? settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  const positionsRealtime = useRealtimeFeed({
    topics: ["account", "positions"],
    environment: activeEnvironment,
    onSnapshotRequired: () => {
      loadAccount(true).catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "account.update" || payload.type === "position.update") {
        loadAccount(true).catch(() => undefined);
        setStatus(payload.type === "position.update" ? "持仓信息有实时更新" : "账户信息有实时更新");
      }
      if (payload.type === "disabled" && ["account", "positions"].includes(payload.topic ?? "")) {
        setStatus(payload.message ?? "私有实时频道未启用");
      }
      if (payload.type === "error" || payload.type === "stale") {
        setStatus(payload.message ?? "实时通道暂不可用，已保留 REST 回退");
      }
    }
  });
  const positions = account?.positions ?? [];
  const openPositions = React.useMemo(() => positions.filter(positionIsOpen), [positions]);
  const visiblePositions = React.useMemo(() => {
    const keyword = positionSearch.trim().toUpperCase();
    return positions
      .filter((item) => !onlyOpen || positionIsOpen(item))
      .filter((item) => sideFilter === "all" || normalizedPositionSide(item.posSide) === sideFilter)
      .filter((item) => !keyword || String(item.instId || "").toUpperCase().includes(keyword))
      .sort((left, right) => {
        const openDelta = Number(positionIsOpen(right)) - Number(positionIsOpen(left));
        if (openDelta) return openDelta;
        const timeDelta = (toNumber(right.uTime) ?? 0) - (toNumber(left.uTime) ?? 0);
        if (timeDelta) return timeDelta;
        return String(left.instId || "").localeCompare(String(right.instId || ""));
      });
  }, [onlyOpen, positionSearch, positions, sideFilter]);

  const totalUpl = openPositions.reduce((sum, item) => sum + (positionNumber(item, ["upl"]) ?? 0), 0);
  const totalNotional = openPositions.reduce((sum, item) => sum + (positionNumber(item, ["notionalUsd"]) ?? 0), 0);
  const totalMargin = openPositions.reduce((sum, item) => sum + (positionNumber(item, ["imr", "margin"]) ?? 0), 0);
  const pnlCounts = React.useMemo(() => openPositions.reduce((counts, item) => {
    const upl = positionNumber(item, ["upl"]);
    if (upl === null) return counts;
    if (upl > 0) counts.profit += 1;
    else if (upl < 0) counts.loss += 1;
    else counts.flat += 1;
    return counts;
  }, { profit: 0, loss: 0, flat: 0 }), [openPositions]);
  const refreshLabel = account?.refresh?.label ?? (account?.warning || accountSourceLabel(account?.source));
  const snapshotTime = account?.refresh?.snapshotTs ?? account?.ts;
  const accountUnavailable = account?.source === "okx-unavailable";
  const tradeEnabled = Boolean(settings?.tradeEnabled);

  const changePositionCloseMode = (
    rowKey: string,
    mode: PositionCloseMode,
    position: Record<string, string>,
    closeOrder: ReturnType<typeof positionCloseOrder>
  ) => {
    setPositionCloseModes((current) => ({ ...current, [rowKey]: mode }));
    if (mode !== "market_all" && closeOrder) {
      setPositionCloseSizes((current) => ({ ...current, [rowKey]: current[rowKey] || closeOrder.sz }));
    }
    if (mode === "limit_reduce") {
      setPositionClosePrices((current) => ({ ...current, [rowKey]: current[rowKey] || positionDefaultClosePrice(position) }));
    }
    setCloseWarning("");
  };

  const closePosition = async (position: Record<string, string>, rowKey: string, mode: PositionCloseMode) => {
    setCloseWarning("");
    if (!account?.configured) {
      setCloseWarning("当前账户未连接，无法提交平仓订单。");
      return;
    }
    if (!tradeEnabled) {
      setCloseWarning(tradeBlockedDetail(settings));
      return;
    }

    const closeOrder = positionCloseOrder(position);
    if (!closeOrder) {
      setCloseWarning("该持仓没有可平数量。");
      return;
    }

    const requestedSize = (positionCloseSizes[rowKey] ?? closeOrder.sz).trim();
    const requestedPrice = (positionClosePrices[rowKey] ?? positionDefaultClosePrice(position)).trim();
    if (mode !== "market_all") {
      const requestedSizeNumber = toNumber(requestedSize);
      const availableSizeNumber = toNumber(closeOrder.sz);
      if (!requestedSizeNumber || requestedSizeNumber <= 0) {
        setCloseWarning("请填写有效的平仓张数。");
        return;
      }
      if (availableSizeNumber !== null && requestedSizeNumber > availableSizeNumber + 1e-12) {
        setCloseWarning(`平仓张数不能超过当前可平 ${closeOrder.sz} 张。`);
        return;
      }
      if (mode === "limit_reduce" && (!requestedPrice || !toNumber(requestedPrice))) {
        setCloseWarning("限价平仓需要填写有效价格。");
        return;
      }
    }

    const environmentName = environmentLabel(activeEnvironment);
    const modeLabel = positionCloseModeLabel(mode);
    const confirmLines = [
      `环境：${environmentName}`,
      `合约：${closeOrder.instId}`,
      `方向：${closeOrder.label}`,
      `方式：${modeLabel}`,
      `当前可平：${closeOrder.sz} 张`
    ];
    if (mode !== "market_all") confirmLines.push(`提交张数：${requestedSize} 张`);
    if (mode === "limit_reduce") confirmLines.push(`委托价格：${requestedPrice}`);
    const liveWarning = activeEnvironment === "live" ? `\n\n注意：这会向 OKX 真实盘提交${modeLabel}请求。` : "";
    if (!(await confirmAction(`确认提交平仓订单？\n${confirmLines.join("\n")}${liveWarning}`))) return;

    setClosingPositionKey(rowKey);
    try {
      const response =
        mode === "market_all"
          ? await fetch(`${API_BASE}/api/trading/positions/close`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                instId: closeOrder.instId,
                mgnMode: positionCloseTradeMode(position),
                posSide: closeOrder.posSide,
                autoCxl: false,
                environment: activeEnvironment
              })
            })
          : await fetch(`${API_BASE}/api/trading/orders`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                instId: closeOrder.instId,
                tdMode: positionCloseTradeMode(position),
                side: closeOrder.side,
                posSide: closeOrder.posSide,
                ordType: positionCloseModeOrderType(mode),
                sz: requestedSize,
                px: mode === "limit_reduce" ? requestedPrice : undefined,
                reduceOnly: true,
                environment: activeEnvironment
              })
            });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "平仓订单提交失败");
      setStatus(`${environmentName}${modeLabel}请求已提交`);
      await loadAccount(true);
    } catch (error) {
      setCloseWarning(error instanceof Error ? error.message : "平仓订单提交失败");
    } finally {
      setClosingPositionKey("");
    }
  };

  return (
    <section className="positionsPage">
      <PageHeader eyebrow="持仓管理" title="OKX 当前持仓" description={`${status}${accountUpdatedAt ? ` · ${new Date(accountUpdatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={<div className="signalLogInlineStats" aria-label="持仓连接状态">
          <Badge className={`signalLogInlineChip ${positionsRealtime.connected ? "live" : "warning"}`}>
            {positionsRealtime.connected ? "实时通道" : "REST 回退"}
          </Badge>
          <Badge className={`signalLogInlineChip ${account?.warning ? "warning" : account?.configured ? "live" : ""}`}>
            {environmentLabel(activeEnvironment)}
          </Badge>
          <Badge className="signalLogInlineChip">持仓 <strong>{openPositions.length}</strong></Badge>
          <Badge className="signalLogInlineChip">名义USD <strong>{formatValue(String(totalNotional))}</strong></Badge>
          <Badge className={`signalLogInlineChip ${pnlValueClass(totalUpl)}`}>未实现盈亏 <strong>{formatSignedValue(totalUpl)}</strong></Badge>
          <Badge className="signalLogInlineChip">{accountRefreshing ? "刷新中" : accountSourceLabel(account?.source)}</Badge>
          <Badge className="signalLogInlineChip">缓存 <strong>{formatDuration(account?.cacheAgeMs)}</strong></Badge>
        </div>} />

      {account?.warning ? <Notice tone="warning">{account.warning}</Notice> : null}
      {closeWarning ? <Notice tone="danger">{closeWarning}</Notice> : null}
      {accountInitialLoading ? <DataLoadingSkeleton label="正在读取当前持仓与账户摘要" /> : null}
      {accountRefreshing && !accountInitialLoading ? <DataLoadingState label="持仓数据更新中，已保留当前内容" compact /> : null}

      <Paper component="section" className="signalLogMinimalPanel positionPnlSummary" p={0} aria-label="未实现盈亏汇总">
        <div className="signalLogMinimalPanelHeader">
          <div>
            <TrendingUp size={17} aria-hidden="true" />
            <strong>未实现盈亏汇总</strong>
          </div>
          <span>{accountSourceLabel(account?.source)}</span>
        </div>
        <div className="positionSummary">
          <MiniMetric label="浮动盈亏合计" value={formatSignedValue(totalUpl)} valueClass={pnlValueClass(totalUpl)} />
          <MiniMetric label="盈利持仓" value={`${pnlCounts.profit} 个`} valueClass="pnl-positive" />
          <MiniMetric label="亏损持仓" value={`${pnlCounts.loss} 个`} valueClass="pnl-negative" />
          <MiniMetric label="持平持仓" value={`${pnlCounts.flat} 个`} valueClass="pnl-neutral" />
          <MiniMetric label="保证金" value={formatValue(String(totalMargin))} />
          <MiniMetric label="名义 USD" value={formatValue(String(totalNotional))} />
        </div>
        <p className="positionPnlSummaryFreshness">
          {refreshLabel}{snapshotTime ? ` · 快照 ${formatTime(String(snapshotTime))}` : ""}
        </p>
      </Paper>

      <section className="signalLogMinimalControls positionMinimalControls" aria-label="持仓筛选">
        <TextInput className="signalLogMinimalSearch" value={positionSearch} onChange={(event) => setPositionSearch(event.target.value.toUpperCase())} placeholder="BTC / ETH / USDT" aria-label="搜索持仓合约" leftSection={<Search size={15} aria-hidden="true" />} size="xs" />
        <SegmentedControl className="signalLogMinimalFilter" aria-label="持仓方向" value={sideFilter} onChange={(value) => setSideFilter(value as PositionSideFilter)} data={positionSideFilters.map((item) => ({ value: item.key, label: item.label }))} size="xs" />
        <Checkbox className="checkField minimalStandaloneCheck" label="只看有仓位" checked={onlyOpen} onChange={(event) => setOnlyOpen(event.target.checked)} />
      </section>

      <Paper component="section" className="signalLogMinimalPanel expanded" p={0}>
        <div className="signalLogMinimalPanelHeader">
          <div>
            <WalletCards size={17} aria-hidden="true" />
            <strong>OKX 持仓列表</strong>
          </div>
          <span>{visiblePositions.length}/{positions.length} 条</span>
        </div>
        <div className="signalLogTableWrap">
          <DataTable className="minimalDataTable positionDataTable">
            <thead>
              <tr>
                <th>合约</th>
                <th>方向</th>
                <th>持仓 / 可平</th>
                <th>均价 / 标记价</th>
                <th>杠杆 / 模式</th>
                <th>保证金 / 名义USD</th>
                <th>盈亏 / 收益率</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {!account?.configured || accountUnavailable ? (
                <tr className="signalLogEmptyRow">
                  <td colSpan={8}>{account?.message ?? "账户和持仓暂不可用"}</td>
                </tr>
              ) : visiblePositions.length === 0 ? (
                <tr className="signalLogEmptyRow">
                  <td colSpan={8}>暂无符合条件的 OKX 持仓</td>
                </tr>
              ) : (
                visiblePositions.map((item, index) => {
                  const upl = positionNumber(item, ["upl"]);
                  const ratio = positionNumber(item, ["uplRatio"]);
                  const rowKey = `${item.instId}-${item.posSide}-${item.posId}-${index}`;
                  const closeOrder = positionCloseOrder(item);
                  const closeMode = positionCloseModes[rowKey] ?? "market_all";
                  const closeSizeValue = positionCloseSizes[rowKey] ?? closeOrder?.sz ?? "";
                  const closePriceValue = positionClosePrices[rowKey] ?? positionDefaultClosePrice(item);
                  const closeDisabled = !tradeEnabled || !closeOrder || closingPositionKey === rowKey;
                  const direction = normalizedPositionSide(item.posSide);
                  const closeOpen = activeCloseRow === rowKey;
                  return (
                    <React.Fragment key={rowKey}>
                      <tr title={`更新时间 ${formatTime(positionText(item, ["uTime", "cTime"], ""))}`}>
                        <td>
                          <strong>{positionText(item, ["instId"])}</strong>
                          <small>{positionText(item, ["ccy"])} 保证金 · {positionText(item, ["instType"], "SWAP")}</small>
                        </td>
                        <td>
                          <Badge className={`signalLogActionTag ${direction === "long" ? "up" : direction === "short" ? "down" : "neutral"}`}>
                            {positionDirectionLabel(item)}
                          </Badge>
                        </td>
                        <td>
                          <strong>{positionQuantityText(item, ["pos"])}</strong>
                          <small>可平 {positionQuantityText(item, ["availPos", "pos"])}</small>
                        </td>
                        <td>
                          <strong>{formatValue(positionText(item, ["avgPx"]))}</strong>
                          <small>标记 {formatValue(positionText(item, ["markPx", "last", "idxPx"]))}</small>
                        </td>
                        <td>
                          <strong>{positionText(item, ["lever"]) === "--" ? "--" : `${formatValue(positionText(item, ["lever"]))}x`}</strong>
                          <small>{positionMarginModeLabel(item.mgnMode)}</small>
                        </td>
                        <td>
                          <strong>{formatValue(positionText(item, ["imr", "margin"]))}</strong>
                          <small>USD {formatValue(positionText(item, ["notionalUsd"]))}</small>
                        </td>
                        <td>
                          <strong className={pnlValueClass(upl)}>{formatSignedValue(upl)}</strong>
                          <small className={pnlValueClass(ratio)}>{formatSignedPercentRatio(ratio)}</small>
                        </td>
                        <td>
                          <Button variant="subtle" size="xs"
                            className="signalLogDetailButton danger"
                            type="button"
                            disabled={!closeOrder || closingPositionKey === rowKey}
                            onClick={() => setActiveCloseRow((current) => current === rowKey ? "" : rowKey)}
                            title={closeOrder ? `可平 ${closeOrder.sz} 张` : "没有可平数量"}
                          >
                            <XCircle size={13} aria-hidden="true" />
                            {closeOpen ? "收起" : "平仓"}
                          </Button>
                        </td>
                      </tr>
                      {closeOpen && closeOrder ? (
                        <tr className="positionCloseExpand">
                          <td colSpan={8}>
                            <div className="compactClosePanel">
                              <div className="closeModeTabs" role="group" aria-label={`${positionText(item, ["instId"])} 平仓方式`}>
                                {positionCloseModeOptions.map((option) => (
                                  <UnstyledButton
                                    key={option.key}
                                    type="button"
                                    className={`closeModeButton ${closeMode === option.key ? "selected" : ""}`}
                                    disabled={closingPositionKey === rowKey}
                                    onClick={() => changePositionCloseMode(rowKey, option.key, item, closeOrder)}
                                    title={positionCloseModeHint(option.key)}
                                    aria-pressed={closeMode === option.key}
                                  >
                                    {option.icon}
                                    <span>{option.label}</span>
                                  </UnstyledButton>
                                ))}
                              </div>
                              <span className="closeModeHint">{positionCloseModeHint(closeMode)}</span>
                              {closeMode !== "market_all" ? (
                                <TextInput
                                  value={closeSizeValue}
                                  inputMode="decimal"
                                  disabled={closingPositionKey === rowKey}
                                  onChange={(event) => {
                                    setPositionCloseSizes((current) => ({ ...current, [rowKey]: event.target.value }));
                                    setCloseWarning("");
                                  }}
                                  placeholder="张数"
                                  aria-label={`${positionText(item, ["instId"])} 平仓张数`}
                                />
                              ) : null}
                              {closeMode === "limit_reduce" ? (
                                <TextInput
                                  value={closePriceValue}
                                  inputMode="decimal"
                                  disabled={closingPositionKey === rowKey}
                                  onChange={(event) => {
                                    setPositionClosePrices((current) => ({ ...current, [rowKey]: event.target.value }));
                                    setCloseWarning("");
                                  }}
                                  placeholder="价格"
                                  aria-label={`${positionText(item, ["instId"])} 平仓价格`}
                                />
                              ) : null}
                              <Button
                                className="primaryButton closeConfirmButton"
                                type="button"
                                disabled={closeDisabled}
                                onClick={() => closePosition(item, rowKey, closeMode)}
                                title={tradeEnabled ? `${positionCloseModeLabel(closeMode)} · ${closeOrder.label} · 可平 ${closeOrder.sz} 张` : tradeBlockedDetail(settings)}
                              >
                                <XCircle size={14} />
                                {closingPositionKey === rowKey ? "提交中" : `确认${positionCloseModeLabel(closeMode)}`}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ) : null}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </DataTable>
        </div>
      </Paper>
    </section>
  );
}

function LlmSettingsPage() {
  const [config, setConfig] = React.useState<LlmConfig | null>(null);
  const [form, setForm] = React.useState<LlmConfigForm>(defaultLlmConfigForm);
  const [status, setStatus] = React.useState("加载中");
  const [saving, setSaving] = React.useState(false);
  const [testing, setTesting] = React.useState(false);
  const [testResult, setTestResult] = React.useState<LlmAnalysis | null>(null);

  const loadConfig = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/llm/config`);
    if (!response.ok) {
      setStatus("AI 配置加载失败");
      return;
    }
    const payload = await response.json();
    const nextConfig = payload.data as LlmConfig;
    setConfig(nextConfig);
    setForm(llmConfigToForm(nextConfig));
    setStatus("AI 配置已加载");
  }, []);

  React.useEffect(() => {
    loadConfig().catch(() => setStatus("AI 配置加载失败"));
  }, [loadConfig]);

  const updateForm = <K extends keyof LlmConfigForm>(key: K, value: LlmConfigForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
    setStatus("配置未保存");
  };

  const selectProviderPreset = (key: string) => {
    const preset = llmProviderPresetByKey(key);
    setForm((current) => {
      const nextModel = preset.key === "custom"
        ? current.model
        : preset.models.includes(current.model)
          ? current.model
          : preset.models[0] ?? current.model;
      return {
        ...current,
        providerPreset: preset.key,
        provider: preset.provider,
        baseUrl: preset.baseUrl || current.baseUrl,
        model: nextModel
      };
    });
    setStatus("配置未保存");
  };

  const selectPresetModel = (value: string) => {
    if (value === "__custom__") {
      setStatus("配置未保存");
      return;
    }
    updateForm("model", value);
  };

  const saveConfig = async (showStatus = true) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/llm/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enabled: form.enabled,
          provider: form.provider,
          baseUrl: form.baseUrl.trim(),
          apiKey: form.apiKey.trim() || undefined,
          clearApiKey: form.clearApiKey,
          model: form.model.trim(),
          temperature: Number(form.temperature),
          maxTokens: Number(form.maxTokens),
          timeoutSeconds: Number(form.timeoutSeconds),
          systemPrompt: form.systemPrompt
        })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "AI 配置保存失败");
      const nextConfig = payload.data as LlmConfig;
      setConfig(nextConfig);
      setForm(llmConfigToForm(nextConfig));
      if (showStatus) {
        setStatus("AI 配置已保存");
        notifications.show({ title: "已保存", message: "AI 配置已更新", color: "green" });
      }
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : "AI 配置保存失败";
      setStatus(message);
      notifications.show({ title: "保存失败", message, color: "red" });
      return false;
    } finally {
      setSaving(false);
    }
  };

  const testConfig = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const saved = await saveConfig(false);
      if (!saved) return;
      const response = await fetch(`${API_BASE}/api/llm/test`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "AI 连接测试失败");
      setTestResult(payload.data as LlmAnalysis);
      setStatus("AI 连接测试通过");
      notifications.show({ title: "连接测试通过", message: `模型 ${form.model || "未知"} 已返回结构化结果`, color: "green" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "AI 连接测试失败";
      setStatus(message);
      notifications.show({ title: "连接测试失败", message, color: "red" });
    } finally {
      setTesting(false);
    }
  };

  const apiKeyStatus = form.apiKey.trim()
    ? "本次将更新"
    : config?.apiKeyConfigured
      ? `已保存 ${config.apiKeyMasked}`
      : "未配置";
  const selectedProviderPreset = llmProviderPresetByKey(form.providerPreset);
  const selectedModelOptions = selectedProviderPreset.models;
  const modelSelectValue = llmModelSelectValue(form.model, selectedModelOptions);
  const selectedModelNote = llmModelNote(selectedProviderPreset, form.model);
  const apiKeyReady = Boolean(config?.apiKeyConfigured || form.apiKey.trim());
  const llmReady = Boolean(form.providerPreset) && form.baseUrl.trim().length > 0 && form.model.trim().length > 0 && apiKeyReady;
  const llmReadinessChecks: { label: string; value: string; ok: boolean }[] = [
    { label: "启用", value: form.enabled ? "已启用" : "未启用", ok: form.enabled },
    { label: "服务商", value: selectedProviderPreset?.label ?? "未选择", ok: Boolean(form.providerPreset) },
    { label: "Base URL", value: form.baseUrl.trim() ? "已填写" : "未填写", ok: form.baseUrl.trim().length > 0 },
    { label: "模型", value: form.model.trim() || "未填写", ok: form.model.trim().length > 0 },
    { label: "API Key", value: apiKeyStatus, ok: apiKeyReady }
  ];

  return (
    <section className="llmPage">
      <PageHeader eyebrow="AI 配置" title="LLM 信号分析" description={`${status}${config?.updatedAt ? ` · ${formatTime(config.updatedAt)}` : ""}`} actions={
        <div className="workspaceActions">
          <div className="statusPills" aria-label="AI 配置状态">
            <Badge className={`statusPill ${form.enabled ? "live" : ""}`}>{form.enabled ? "已启用" : "未启用"}</Badge>
            <Badge className={`statusPill ${config?.apiKeyConfigured || form.apiKey.trim() ? "live" : "warning"}`}>{apiKeyStatus}</Badge>
          </div>
          <IconButton label="刷新 AI 配置" onClick={() => loadConfig().catch(() => setStatus("AI 配置加载失败"))}>
            <RefreshCw size={16} />
          </IconButton>
        </div>
      } />
      {status === "加载中" ? <DataLoadingState label="正在读取 AI 配置" compact /> : null}

      <Notice tone="info">LLM 可作为自动交易信号来源；系统只在 OKX 虚拟盘按风控执行，真实盘不会自动下单。</Notice>

      <section className="llmSummary">
        <Metric label="启用状态" value={form.enabled ? "启用" : "关闭"} valueClass={form.enabled ? "up" : ""} />
        <Metric label="服务商" value={selectedProviderPreset.label} />
        <Metric label="模型" value={form.model || "--"} />
        <Metric label="温度" value={form.temperature || "--"} />
        <Metric label="超时" value={`${form.timeoutSeconds || "--"} 秒`} />
        <Metric label="API Key" value={apiKeyStatus} />
      </section>

      <section className="llmGrid">
        <section className="positionsPanel llmConfigPanel">
          <PanelHeader icon={<BrainCircuit size={17} />} title="模型连接" meta={saving ? "保存中" : "本地保存"} />
          <div className="llmForm">
            <Checkbox className="checkField llmEnable" label="启用 LLM 信号分析" checked={form.enabled}
              onChange={(event) => updateForm("enabled", event.target.checked)} />
            <div className="fieldGrid">
              <label className="fieldBlock">
                <span>服务商预设</span>
                <Select value={form.providerPreset} onChange={(value) => value && selectProviderPreset(value)}
                  data={llmProviderPresets.map((item) => ({ value: item.key, label: item.label }))} />
              </label>
              <label className="fieldBlock">
                <span>推荐模型</span>
                <Select
                  value={modelSelectValue}
                  onChange={(value) => value && selectPresetModel(value)}
                  disabled={selectedModelOptions.length === 0}
                  searchable
                  maxDropdownHeight={280}
                  nothingFoundMessage="未找到匹配的模型"
                  data={[
                    ...selectedModelOptions.map((model) => ({
                      value: model,
                      label: model,
                      description: llmModelNote(selectedProviderPreset, model)
                    })),
                    { value: "__custom__", label: "自定义 / 手动填写", description: "选择后在下方手动填写任意模型名称" }
                  ]}
                  renderOption={({ option }) => {
                    const description = (option as { description?: string }).description;
                    return (
                      <div style={{ display: "flex", flexDirection: "column", gap: 2, width: "100%" }}>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{option.label}</span>
                        {description ? (
                          <span style={{ fontSize: 12, color: "var(--color-muted-strong)", lineHeight: 1.3 }}>{description}</span>
                        ) : null}
                      </div>
                    );
                  }}
                />
              </label>
            </div>
            <div className="providerPresetHint">
              <BrainCircuit size={15} aria-hidden="true" />
              <span>
                {selectedProviderPreset.note}
                {selectedModelNote ? ` 当前模型：${selectedModelNote}。` : ""}
                {selectedProviderPreset.pricingNote ? ` ${selectedProviderPreset.pricingNote}` : ""}
              </span>
            </div>
            <div className="fieldGrid">
              <label className="fieldBlock">
                <span>Base URL</span>
                <TextInput
                  value={form.baseUrl}
                  onChange={(event) => updateForm("baseUrl", event.target.value)}
                  placeholder="https://api.openai.com/v1"
                />
              </label>
              <label className="fieldBlock">
                <span>自定义模型名称（可选）</span>
                <TextInput value={form.model} onChange={(event) => updateForm("model", event.target.value)} placeholder="例如 deepseek-flash" />
                <span style={{ fontSize: 12, color: "var(--color-muted-strong)" }}>下拉未列出时，可在此手动填写任意模型名称</span>
              </label>
            </div>
            <PasswordInput className="fieldBlock" label="API Key" value={form.apiKey}
              onChange={(event) => updateForm("apiKey", event.target.value)}
              placeholder={config?.apiKeyConfigured ? `保留已保存 Key：${config.apiKeyMasked}` : "填写你的 LLM API Key"} />
            <Checkbox className="checkField" label="清除已保存 API Key" checked={form.clearApiKey}
              onChange={(event) => updateForm("clearApiKey", event.target.checked)} disabled={!config?.apiKeyConfigured} />
            <Disclosure
              className="llmAdvancedDisclosure"
              label={
                <>
                  <SlidersHorizontal size={14} aria-hidden="true" />
                  高级参数（Temperature / 最大 Token / 超时 / 系统 Prompt）
                </>
              }
            >
              <div className="fieldGrid">
                <label className="fieldBlock">
                  <span>Temperature</span>
                  <TextInput inputMode="decimal" value={form.temperature} onChange={(event) => updateForm("temperature", event.target.value)} />
                </label>
                <label className="fieldBlock">
                  <span>最大输出 Token</span>
                  <TextInput inputMode="numeric" value={form.maxTokens} onChange={(event) => updateForm("maxTokens", event.target.value)} />
                </label>
              </div>
              <label className="fieldBlock">
                <span>超时秒数</span>
                <TextInput inputMode="numeric" value={form.timeoutSeconds} onChange={(event) => updateForm("timeoutSeconds", event.target.value)} />
              </label>
              <label className="fieldBlock">
                <span>系统 Prompt</span>
                <Textarea value={form.systemPrompt} onChange={(event) => updateForm("systemPrompt", event.target.value)} minRows={7} autosize />
              </label>
            </Disclosure>
            <div className="llmActions">
              <Button className="secondaryButton" variant="default" type="button" onClick={testConfig} disabled={saving || testing}>
                <Send size={15} />
                {testing ? "测试中" : "保存并测试"}
              </Button>
              <Button className="primaryButton" type="button" onClick={() => saveConfig()} disabled={saving || testing}>
                <Check size={15} />
                {saving ? "保存中" : "保存配置"}
              </Button>
            </div>
          </div>
        </section>

        <section className="positionsPanel llmStatusPanel">
          <PanelHeader icon={<Check size={17} />} title="配置状态" meta="实时" />
          <div className="llmStatusBody">
            <div className="llmCheckList">
              {llmReadinessChecks.map((item) => (
                <div key={item.label} className={`llmCheckItem ${item.ok ? "ok" : "todo"}`}>
                  <span className="llmCheckDot" aria-hidden="true" />
                  <span className="llmCheckLabel">{item.label}</span>
                  <span className="llmCheckValue">{item.value}</span>
                </div>
              ))}
            </div>
            <div className={`llmReadiness ${llmReady ? "ok" : "warn"}`}>
              {llmReady ? "配置完整，可保存并测试" : "请补全必填项后再测试"}
            </div>
            {testResult ? (
              <div className="aiAnalysisPanel testResult">
                <div className="aiAnalysisHeader">
                  <div>
                    <BrainCircuit size={18} aria-hidden="true" />
                    <strong>测试结果</strong>
                  </div>
                  <Badge className="statusPill live">连接正常</Badge>
                </div>
                <p className="aiSummary">{testResult.summary || "LLM 已返回结构化结果。"}</p>
                <div className="aiAnalysisGrid">
                  <Metric label="模型" value={testResult.model || form.model || "--"} />
                  <Metric label="建议" value={llmRecommendationLabel(testResult.recommendation)} />
                  <Metric label="置信度" value={`${testResult.confidence ?? 0}%`} />
                  <Metric label="总 Token" value={formatTokenCount(Number(testResult.usage?.total_tokens ?? 0))} />
                  <Metric label="输入 / 输出" value={`${formatTokenCount(Number(testResult.usage?.prompt_tokens ?? 0))} / ${formatTokenCount(Number(testResult.usage?.completion_tokens ?? 0))}`} />
                  <Metric label="耗时" value={formatLatency(Number(testResult.usage?.duration_ms ?? testResult.duration_ms ?? 0))} />
                </div>
              </div>
            ) : (
              <div className="signalReasonBox muted">
                <strong>验证连接</strong>
                <p>点击「保存并测试」后，这里显示 LLM 返回的结构化结果。</p>
              </div>
            )}
          </div>
        </section>
      </section>
    </section>
  );
}

function AccountPage() {
  const [account, setAccount] = React.useState<AccountResponse | null>(null);
  const [settings, setSettings] = React.useState<SettingsStatus | null>(null);
  const [status, setStatus] = React.useState("加载中");
  const [accountUpdatedAt, setAccountUpdatedAt] = React.useState<number | null>(null);
  const [accountRefreshing, setAccountRefreshing] = React.useState(false);
  const [onlyNonZeroAssets, setOnlyNonZeroAssets] = React.useState(true);
  const [assetSearch, setAssetSearch] = React.useState("");
  const accountLoadingRef = React.useRef(false);
  const accountInitialLoading = accountRefreshing && !account;

  const loadAccount = React.useCallback(async (force = false) => {
    if (accountLoadingRef.current) return;
    accountLoadingRef.current = true;
    setAccountRefreshing(true);
    try {
      const response = await fetch(`${API_BASE}/api/account${force ? "?force=true" : ""}`);
      if (!response.ok) {
        setAccount((current) => accountFailureSnapshot(current, "账户数据"));
        setStatus("账户接口异常");
        return;
      }
      const payload = await response.json();
      setAccount(payload);
      setAccountUpdatedAt(Date.now());
      if (!payload.configured) {
        setStatus("未配置 API Key");
      } else if (payload.warning) {
        setStatus("连接波动，已显示可用缓存");
      } else {
        setStatus(payload.source === "okx" ? "账户信息已实时更新" : "账户信息已加载");
      }
    } catch {
      setAccount((current) => accountFailureSnapshot(current, "账户数据"));
      setStatus("账户接口异常");
    } finally {
      accountLoadingRef.current = false;
      setAccountRefreshing(false);
    }
  }, []);

  const loadSettings = React.useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/settings/status`);
    if (!response.ok) return;
    const payload = await response.json();
    setSettings(payload);
  }, []);

  React.useEffect(() => {
    loadAccount().catch(() => setStatus("账户信息加载失败"));
    loadSettings().catch(() => undefined);
    const refreshVisibleAccount = () => {
      if (!document.hidden) {
        loadAccount().catch(() => undefined);
      }
    };
    const timer = window.setInterval(() => {
      refreshVisibleAccount();
    }, ACCOUNT_POLL_MS);
    document.addEventListener("visibilitychange", refreshVisibleAccount);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshVisibleAccount);
    };
  }, [loadAccount, loadSettings]);

  const activeEnvironment = account?.environment ?? settings?.tradingEnvironment ?? (settings?.simulatedTrading ? "simulated" : "live");
  const accountRealtime = useRealtimeFeed({
    topics: ["account"],
    environment: activeEnvironment,
    onSnapshotRequired: () => {
      loadAccount(true).catch(() => undefined);
    },
    onEvent: (payload) => {
      if (payload.type === "account.update") {
        loadAccount(true).catch(() => undefined);
        setStatus("账户信息有实时更新");
      }
      if (payload.type === "disabled" && payload.topic === "account") {
        setStatus(payload.message ?? "私有实时频道未启用");
      }
      if (payload.type === "error" || payload.type === "stale") {
        setStatus(payload.message ?? "实时通道暂不可用，已保留 REST 回退");
      }
    }
  });
  const summary = account?.summary ?? {};
  const details = accountDetails(summary);
  const positions = account?.positions ?? [];
  const totalUpl = positions.reduce((sum, item) => sum + Number(item.upl ?? 0), 0);
  const profitablePositions = positions.filter((item) => Number(item.upl ?? 0) >= 0).length;
  const nonZeroAssetDetails = React.useMemo(() => details.filter(accountDetailIsNonZero), [details]);
  const visibleAssetDetails = React.useMemo(() => {
    const keyword = assetSearch.trim().toUpperCase();
    const rows = onlyNonZeroAssets ? nonZeroAssetDetails : details;
    return [...rows]
      .filter((item) => !keyword || accountDetailCurrency(item).toUpperCase().includes(keyword))
      .sort((left, right) => {
        const usdDelta = accountDetailUsdValue(right) - accountDetailUsdValue(left);
        if (usdDelta !== 0) return usdDelta;
        return accountDetailCurrency(left).localeCompare(accountDetailCurrency(right));
      });
  }, [assetSearch, details, nonZeroAssetDetails, onlyNonZeroAssets]);
  const totalEquity = firstMetric(summary, details, "totalEq", ["eqUsd"]);
  const detailEquityUsd = sumDetails(details, ["eqUsd"]);
  const marginAssetCount = details.filter((item) => accountDetailAnyNonZero(item, ["imr", "mmr"])).length;
  const frozenAssetCount = details.filter((item) => accountDetailAnyNonZero(item, ["frozenBal", "ordFrozen"])).length;

  return (
    <section className="accountPage">
      <PageHeader eyebrow="账户管理" title="OKX 账户信息" description={`${status}${accountUpdatedAt ? ` · ${new Date(accountUpdatedAt).toLocaleTimeString("zh-CN")}` : ""}`} actions={<div className="signalLogInlineStats" aria-label="账户连接状态">
          <Badge className={`signalLogInlineChip ${accountRealtime.connected ? "live" : "warning"}`}>
            {accountRealtime.connected ? "实时通道" : "REST 回退"}
          </Badge>
          <Badge className={`signalLogInlineChip ${account?.warning ? "warning" : account?.configured ? "live" : ""}`}>
            {accountRefreshing ? "刷新中" : accountSourceLabel(account?.source)}
          </Badge>
          <Badge className="signalLogInlineChip">总权益 <strong>{formatValue(totalEquity)}</strong></Badge>
          <Badge className="signalLogInlineChip">非零币种 <strong>{nonZeroAssetDetails.length}</strong></Badge>
          <Badge className="signalLogInlineChip">持仓 <strong>{positions.length}</strong></Badge>
          <Badge className="signalLogInlineChip">缓存 <strong>{formatDuration(account?.cacheAgeMs)}</strong></Badge>
        </div>} />

      {account?.warning ? <Notice tone="warning">{account.warning}</Notice> : null}
      {accountInitialLoading ? <DataLoadingSkeleton label="正在读取账户资产与余额" /> : null}
      {accountRefreshing && !accountInitialLoading ? <DataLoadingState label="账户数据更新中，已保留当前内容" compact /> : null}

      <section className="signalLogMinimalControls accountMinimalControls" aria-label="资产筛选">
        <TextInput
          className="signalLogMinimalSearch"
          value={assetSearch}
          onChange={(event) => setAssetSearch(event.target.value.toUpperCase())}
          placeholder="搜索 BTC / ETH / USDT"
          aria-label="搜索币种资产"
          leftSection={<Search size={15} aria-hidden="true" />}
          size="xs"
        />
        <SegmentedControl
          className="signalLogMinimalFilter accountAssetMode"
          aria-label="资产范围"
          value={onlyNonZeroAssets ? "nonzero" : "all"}
          onChange={(value) => setOnlyNonZeroAssets(value === "nonzero")}
          data={[{ value: "nonzero", label: "非零资产" }, { value: "all", label: "全部币种" }]}
          size="xs"
        />
      </section>

      <Paper component="section" className="signalLogMinimalPanel accountAssetPanel" p={0}>
        <div className="signalLogMinimalPanelHeader">
          <div>
            <WalletCards size={17} aria-hidden="true" />
            <strong>币种资产</strong>
          </div>
          <span>{visibleAssetDetails.length}/{details.length} 个币种</span>
        </div>
        <div className="signalLogTableWrap">
          <DataTable className="minimalDataTable assetDataTable">
            <thead>
              <tr>
                <th>币种</th>
                <th>总权益</th>
                <th>可用权益</th>
                <th>现金余额</th>
                <th>冻结</th>
                <th>保证金</th>
                <th>USD 估值</th>
                <th>未实现盈亏</th>
                <th>更新时间</th>
              </tr>
            </thead>
            <tbody>
              {!account?.configured ? (
                <tr className="signalLogEmptyRow">
                  <td colSpan={9}>{account?.message ?? "未配置 OKX API Key"}</td>
                </tr>
              ) : visibleAssetDetails.length ? (
                visibleAssetDetails.map((item) => {
                  const currency = accountDetailCurrency(item);
                  const upl = accountDetailNumber(item, ["upl"]) ?? 0;
                  return (
                    <tr key={currency}>
                      <td>
                        <strong>{currency}</strong>
                        <small>{accountDetailIsNonZero(item) ? "非零资产" : "零资产"}</small>
                      </td>
                      <td>{formatValue(accountDetailText(item, ["eq"]))}</td>
                      <td>{formatValue(accountDetailText(item, ["availEq", "availBal"]))}</td>
                      <td>{formatValue(accountDetailText(item, ["cashBal"]))}</td>
                      <td>{formatValue(accountDetailText(item, ["frozenBal", "ordFrozen"]))}</td>
                      <td>
                        <strong>{formatValue(accountDetailText(item, ["imr"]))}</strong>
                        <small>维持 {formatValue(accountDetailText(item, ["mmr"]))}</small>
                      </td>
                      <td>{formatValue(accountDetailText(item, ["eqUsd"]))}</td>
                      <td>
                        <strong className={upl >= 0 ? "up" : "down"}>{formatValue(accountDetailText(item, ["upl"]))}</strong>
                      </td>
                      <td>{formatTime(accountDetailText(item, ["uTime"], ""))}</td>
                    </tr>
                  );
                })
              ) : (
                <tr className="signalLogEmptyRow">
                  <td colSpan={9}>暂无{onlyNonZeroAssets ? "非零" : ""}币种资产</td>
                </tr>
              )}
            </tbody>
          </DataTable>
        </div>
      </Paper>
    </section>
  );
}

function PanelHeader({
  icon,
  title,
  meta,
  action
}: {
  icon: React.ReactNode;
  title: string;
  meta?: string;
  action?: React.ReactNode;
}) {
  return (
    <Group className="panelHeader" justify="space-between" gap="sm">
      <Group gap="xs">
        <ThemeIcon variant="light" color="workspace" size="sm">{icon}</ThemeIcon>
        <Text fw={750} size="sm">{title}</Text>
      </Group>
      {meta ? <Text c="dimmed" size="xs">{meta}</Text> : null}
      {action}
    </Group>
  );
}

function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className = ""
}: {
  eyebrow?: string;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <Group component="header" className={`workspaceHeader ${className}`.trim()} justify="space-between" align="flex-start" gap="md">
      <Stack gap="xs">
        {eyebrow ? <Text component="span" className="eyebrow" size="xs">{eyebrow}</Text> : null}
        <Text component="h1" inherit>{title}</Text>
        {description ? <Text component="p" size="sm" c="dimmed">{description}</Text> : null}
      </Stack>
      {actions}
    </Group>
  );
}

function IconButton({ children, label, onClick }: { children: React.ReactNode; label: string; onClick: () => void }) {
  return (
    <ActionIcon className="iconButton" onClick={onClick} title={label} aria-label={label} variant="subtle" color="workspace">
      {children}
    </ActionIcon>
  );
}

function DataTable({ className, children }: { className?: string; children: React.ReactNode }) {
  return <Table className={className} highlightOnHover>{children}</Table>;
}

function SelectableTableRow({ children, onSelect, selected, title }: { children: React.ReactNode; onSelect: () => void; selected?: boolean; title?: string }) {
  return <Table.Tr
    tabIndex={0}
    aria-selected={selected}
    title={title}
    onClick={onSelect}
    onKeyDown={(event) => {
      if (event.target !== event.currentTarget || (event.key !== "Enter" && event.key !== " ")) return;
      event.preventDefault();
      onSelect();
    }}
  >{children}</Table.Tr>;
}

function Metric({ label, value, valueClass = "" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={valueClass}>{value}</strong>
    </div>
  );
}

function MiniMetric({ label, value, valueClass = "" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="miniMetric">
      <span>{label}</span>
      <strong className={valueClass}>{value}</strong>
    </div>
  );
}

function CandleInspectorMetric({
  label,
  value,
  valueClass = "",
  featured = false
}: {
  label: string;
  value: string;
  valueClass?: string;
  featured?: boolean;
}) {
  return (
    <div className={`candleInspectorMetric ${featured ? "featured" : ""}`} title={`${label}：${value}`}>
      <span>{label}</span>
      <strong className={valueClass}>{value}</strong>
    </div>
  );
}

function InfoTile({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="infoTile">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

type ConfirmAction = (message: string) => Promise<boolean>;

const ConfirmActionContext = React.createContext<ConfirmAction | null>(null);

function useConfirmAction(): ConfirmAction {
  const confirmAction = React.useContext(ConfirmActionContext);
  if (!confirmAction) throw new Error("确认操作组件尚未就绪");
  return confirmAction;
}

function ConfirmActionProvider({ children }: { children: React.ReactNode }) {
  const [message, setMessage] = React.useState<string | null>(null);
  const pendingRef = React.useRef<((accepted: boolean) => void) | null>(null);

  const finish = React.useCallback((accepted: boolean) => {
    const resolve = pendingRef.current;
    pendingRef.current = null;
    setMessage(null);
    resolve?.(accepted);
  }, []);

  const confirmAction = React.useCallback<ConfirmAction>((nextMessage) => {
    if (pendingRef.current) return Promise.resolve(false);
    return new Promise<boolean>((resolve) => {
      pendingRef.current = resolve;
      setMessage(nextMessage);
    });
  }, []);

  React.useEffect(() => () => {
    pendingRef.current?.(false);
    pendingRef.current = null;
  }, []);

  return (
    <ConfirmActionContext.Provider value={confirmAction}>
      {children}
      <Modal
        opened={message !== null}
        onClose={() => finish(false)}
        title="确认操作"
        centered
        closeOnClickOutside={false}
        closeButtonProps={{ "aria-label": "取消并关闭确认框" }}
      >
        <Text component="p" className="confirmActionCopy" size="sm">{message}</Text>
        <Group justify="flex-end" gap="sm" mt="md">
          <Button type="button" variant="default" onClick={() => finish(false)}>取消</Button>
          <Button type="button" color={message?.includes("真实盘") ? "red" : "workspace"} onClick={() => finish(true)}>确认执行</Button>
        </Group>
      </Modal>
    </ConfirmActionContext.Provider>
  );
}

const rootElement = document.getElementById("root")!;
const root = window.__okxDashboardRoot ?? createRoot(rootElement);
window.__okxDashboardRoot = root;
root.render(
  <MantineProvider theme={mantineTheme} defaultColorScheme="light">
    <IconContext.Provider value={{ weight: "regular", "aria-hidden": true }}>
      <DatesProvider settings={{ locale: "zh-cn", firstDayOfWeek: 1 }}>
        <Notifications position="bottom-right" limit={3} />
        <ConfirmActionProvider><App /></ConfirmActionProvider>
      </DatesProvider>
    </IconContext.Provider>
  </MantineProvider>
);

declare global {
  interface Window {
    __okxDashboardRoot?: ReturnType<typeof createRoot>;
  }
}
