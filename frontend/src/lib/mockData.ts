export type Rating = "BUY" | "HOLD" | "SELL";
export type RiskLevel = "Low" | "Medium" | "High";

export interface CompanyData {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  description: string;
  price: number;
  change: number; // %
  marketCap: string;
  rating: Rating;
  intrinsicValue: number;
  upside: number; // %
  wacc: number;
  terminalGrowth: number;
  stats: { revenue: string; eps: string; pe: string; evEbitda: string };
  peers: { ticker: string; pe: number; ev: number; pb: number }[];
  sensitivity: number[][]; // 5x5
  monteCarlo: { v: number; freq: number }[];
  risk: {
    level: RiskLevel;
    beta: number;
    sharpe: number;
    maxDrawdown: number;
    var95: number;
    altmanZ: number;
    debtToEquity: number;
    interestCoverage: number;
    currentRatio: number;
  };
  sentiment: {
    score: number; // 0-100
    yoyShift: number; // %
    keywords: { word: string; weight: number; tone: "pos" | "neg" | "neu" }[];
    redFlags: string[];
  };
  memo: {
    summary: string;
    performance: string;
    bear: number;
    base: number;
    bull: number;
    risks: string[];
    thesis: string;
    bearCase: string;
  };
}

const mc = (mu: number, span: number) => {
  // simple bell-curve mock
  const out: { v: number; freq: number }[] = [];
  for (let i = 0; i < 25; i++) {
    const x = mu - span + (i * (span * 2)) / 24;
    const z = (x - mu) / (span / 2.5);
    const f = Math.exp(-(z * z) / 2);
    out.push({ v: +x.toFixed(1), freq: +(f * 100).toFixed(1) });
  }
  return out;
};

const sens = (mid: number) =>
  Array.from({ length: 5 }, (_, r) =>
    Array.from({ length: 5 }, (_, c) => +(mid * (0.85 + r * 0.07 + c * 0.02)).toFixed(1)),
  );

export const COMPANIES: Record<string, CompanyData> = {
  AAPL: {
    ticker: "AAPL",
    name: "Apple Inc.",
    sector: "Technology",
    industry: "Consumer Electronics",
    description:
      "Apple designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories worldwide, with a rapidly-growing high-margin services franchise.",
    price: 176.85,
    change: 1.24,
    marketCap: "$2.71T",
    rating: "BUY",
    intrinsicValue: 198.4,
    upside: 12.2,
    wacc: 8.4,
    terminalGrowth: 2.5,
    stats: { revenue: "$391.0B", eps: "$6.42", pe: "27.6x", evEbitda: "21.3x" },
    peers: [
      { ticker: "AAPL", pe: 27.6, ev: 21.3, pb: 47.5 },
      { ticker: "MSFT", pe: 33.8, ev: 24.1, pb: 11.9 },
      { ticker: "GOOGL", pe: 23.4, ev: 17.2, pb: 6.7 },
      { ticker: "META", pe: 25.1, ev: 16.5, pb: 8.4 },
    ],
    sensitivity: sens(198),
    monteCarlo: mc(198, 50),
    risk: {
      level: "Medium",
      beta: 1.21,
      sharpe: 1.42,
      maxDrawdown: -28.4,
      var95: -3.1,
      altmanZ: 6.8,
      debtToEquity: 1.51,
      interestCoverage: 28.6,
      currentRatio: 0.92,
    },
    sentiment: {
      score: 72,
      yoyShift: 4.2,
      keywords: [
        { word: "services growth", weight: 92, tone: "pos" },
        { word: "AI integration", weight: 88, tone: "pos" },
        { word: "China demand", weight: 71, tone: "neg" },
        { word: "regulatory pressure", weight: 64, tone: "neg" },
        { word: "margin expansion", weight: 78, tone: "pos" },
        { word: "supply chain", weight: 52, tone: "neu" },
      ],
      redFlags: ["China revenue concentration", "App Store regulatory risk"],
    },
    memo: {
      summary:
        "Apple is a high-quality compounder transitioning from hardware-led growth to a services and platform model, supported by a 2.2B-device installed base.",
      performance:
        "FY24 revenue of $391B (flat YoY) was masked by FX and a Mac/iPad reset; Services grew 13% YoY to $96B and now represents 25% of revenue at ~74% gross margin.",
      bear: 158,
      base: 198,
      bull: 232,
      risks: [
        "China iPhone demand softening on local competition",
        "Regulatory pressure on App Store take-rate (DOJ, EU DMA)",
        "Generative AI execution risk vs. cloud hyperscalers",
      ],
      thesis:
        "Services momentum and gross-margin expansion underpin a $198 base case (~12% upside). Re-rating optionality from on-device AI and Vision platform.",
      bearCase:
        "China iPhone revenue declines 15% over two years and App Store take-rate is forced to 15%, compressing services margin and producing a $158 fair value.",
    },
  },
  TSLA: {
    ticker: "TSLA",
    name: "Tesla, Inc.",
    sector: "Consumer Discretionary",
    industry: "Auto Manufacturers",
    description: "Tesla designs, develops, manufactures and sells electric vehicles, energy generation and storage systems, and provides related services.",
    price: 248.12,
    change: -0.86,
    marketCap: "$789B",
    rating: "HOLD",
    intrinsicValue: 214.1,
    upside: -13.7,
    wacc: 11.2,
    terminalGrowth: 3.0,
    stats: { revenue: "$96.8B", eps: "$2.27", pe: "109.3x", evEbitda: "58.4x" },
    peers: [
      { ticker: "TSLA", pe: 109.3, ev: 58.4, pb: 14.2 },
      { ticker: "TM", pe: 7.8, ev: 11.2, pb: 1.1 },
      { ticker: "GM", pe: 5.6, ev: 8.7, pb: 0.9 },
      { ticker: "F", pe: 12.1, ev: 14.5, pb: 1.0 },
    ],
    sensitivity: sens(214),
    monteCarlo: mc(214, 70),
    risk: {
      level: "High",
      beta: 2.04,
      sharpe: 0.81,
      maxDrawdown: -73.6,
      var95: -6.4,
      altmanZ: 4.1,
      debtToEquity: 0.18,
      interestCoverage: 18.3,
      currentRatio: 1.86,
    },
    sentiment: {
      score: 54,
      yoyShift: -8.4,
      keywords: [
        { word: "FSD progress", weight: 84, tone: "pos" },
        { word: "Robotaxi", weight: 79, tone: "pos" },
        { word: "price cuts", weight: 81, tone: "neg" },
        { word: "China competition", weight: 76, tone: "neg" },
        { word: "energy storage", weight: 68, tone: "pos" },
        { word: "execution risk", weight: 60, tone: "neg" },
      ],
      redFlags: ["Margin compression", "FSD timeline slippage", "Key-person risk"],
    },
    memo: {
      summary: "Tesla is priced as an AI/robotics platform but financially performs as an auto OEM under cyclical pressure.",
      performance: "Auto gross margin compressed to 18.4% (from 26.5% peak) on price cuts; Energy and Services growing 40%+ but still <15% of revenue.",
      bear: 142,
      base: 214,
      bull: 320,
      risks: ["Sustained margin compression", "Robotaxi monetization timeline", "Regulatory risk on autonomy"],
      thesis: "Optionality on FSD/Robotaxi is real but unpriced cleanly. At ~110x earnings the bar for execution is extreme.",
      bearCase: "FSD remains driver-supervised through 2027, auto margins stabilise at 16% — fair value contracts to $142.",
    },
  },
  GOOGL: {
    ticker: "GOOGL",
    name: "Alphabet Inc.",
    sector: "Communication Services",
    industry: "Internet Content & Information",
    description: "Alphabet provides online advertising services, cloud platform, hardware and a portfolio of moonshot bets through Other Bets.",
    price: 172.3,
    change: 0.98,
    marketCap: "$2.13T",
    rating: "BUY",
    intrinsicValue: 205.6,
    upside: 19.3,
    wacc: 9.1,
    terminalGrowth: 3.0,
    stats: { revenue: "$350.0B", eps: "$8.04", pe: "23.4x", evEbitda: "17.2x" },
    peers: [
      { ticker: "GOOGL", pe: 23.4, ev: 17.2, pb: 6.7 },
      { ticker: "META", pe: 25.1, ev: 16.5, pb: 8.4 },
      { ticker: "MSFT", pe: 33.8, ev: 24.1, pb: 11.9 },
      { ticker: "AMZN", pe: 42.2, ev: 18.4, pb: 7.9 },
    ],
    sensitivity: sens(205),
    monteCarlo: mc(205, 45),
    risk: {
      level: "Low",
      beta: 1.05,
      sharpe: 1.68,
      maxDrawdown: -22.1,
      var95: -2.6,
      altmanZ: 8.4,
      debtToEquity: 0.11,
      interestCoverage: 121.4,
      currentRatio: 2.17,
    },
    sentiment: {
      score: 78,
      yoyShift: 6.1,
      keywords: [
        { word: "Gemini adoption", weight: 90, tone: "pos" },
        { word: "Cloud margin", weight: 86, tone: "pos" },
        { word: "search disruption", weight: 72, tone: "neg" },
        { word: "antitrust", weight: 65, tone: "neg" },
        { word: "YouTube growth", weight: 81, tone: "pos" },
        { word: "Capex", weight: 58, tone: "neu" },
      ],
      redFlags: ["DOJ search remedy uncertainty"],
    },
    memo: {
      summary: "Alphabet remains the most profitable AI infrastructure beneficiary with the broadest distribution.",
      performance: "Search revenue grew 12% YoY despite generative AI overhang; Cloud op margin expanded to 17%.",
      bear: 168,
      base: 205,
      bull: 248,
      risks: ["DOJ search remedy", "AI substitution in search", "Capex intensity"],
      thesis: "Cloud margin expansion + Gemini distribution support 19% upside; the stock under-prices the AI infrastructure tailwind.",
      bearCase: "Forced search remedy reduces query monetization 10%; fair value compresses to $168.",
    },
  },
  MSFT: {
    ticker: "MSFT",
    name: "Microsoft Corporation",
    sector: "Technology",
    industry: "Software—Infrastructure",
    description: "Microsoft develops and supports software, services, devices and solutions, with a leading cloud platform (Azure) and a deep enterprise franchise.",
    price: 428.55,
    change: 0.62,
    marketCap: "$3.18T",
    rating: "BUY",
    intrinsicValue: 462.0,
    upside: 7.8,
    wacc: 8.8,
    terminalGrowth: 3.0,
    stats: { revenue: "$245.1B", eps: "$11.80", pe: "33.8x", evEbitda: "24.1x" },
    peers: [
      { ticker: "MSFT", pe: 33.8, ev: 24.1, pb: 11.9 },
      { ticker: "GOOGL", pe: 23.4, ev: 17.2, pb: 6.7 },
      { ticker: "ORCL", pe: 28.4, ev: 19.6, pb: 22.4 },
      { ticker: "CRM", pe: 47.1, ev: 26.1, pb: 4.8 },
    ],
    sensitivity: sens(462),
    monteCarlo: mc(462, 80),
    risk: {
      level: "Low",
      beta: 0.93,
      sharpe: 1.85,
      maxDrawdown: -19.4,
      var95: -2.3,
      altmanZ: 9.1,
      debtToEquity: 0.31,
      interestCoverage: 41.2,
      currentRatio: 1.27,
    },
    sentiment: {
      score: 81,
      yoyShift: 5.4,
      keywords: [
        { word: "Azure AI", weight: 94, tone: "pos" },
        { word: "Copilot revenue", weight: 88, tone: "pos" },
        { word: "Capex intensity", weight: 71, tone: "neg" },
        { word: "OpenAI dependency", weight: 64, tone: "neu" },
        { word: "M365 attach", weight: 79, tone: "pos" },
      ],
      redFlags: ["Capex visibility beyond FY26"],
    },
    memo: {
      summary: "Microsoft is the deepest enterprise AI distribution play, monetising through Azure consumption and Copilot SKUs.",
      performance: "Azure grew 33% YoY in constant currency; AI services contributed ~7pts of growth.",
      bear: 380,
      base: 462,
      bull: 540,
      risks: ["Capex digestion", "OpenAI relationship terms", "On-prem cannibalisation"],
      thesis: "Azure AI franchise should drive durable mid-teens top-line for 3+ years; current multiple is reasonable for the quality.",
      bearCase: "AI capex doesn't translate to margin in FY26; multiple compresses to 28x for $380 fair value.",
    },
  },
  NVDA: {
    ticker: "NVDA",
    name: "NVIDIA Corporation",
    sector: "Technology",
    industry: "Semiconductors",
    description: "NVIDIA designs and supplies graphics processors, accelerated computing platforms and AI infrastructure software for data centers, gaming and automotive.",
    price: 138.4,
    change: 2.41,
    marketCap: "$3.39T",
    rating: "BUY",
    intrinsicValue: 162.2,
    upside: 17.2,
    wacc: 10.4,
    terminalGrowth: 3.5,
    stats: { revenue: "$130.5B", eps: "$2.95", pe: "46.9x", evEbitda: "38.1x" },
    peers: [
      { ticker: "NVDA", pe: 46.9, ev: 38.1, pb: 51.2 },
      { ticker: "AMD", pe: 41.3, ev: 31.2, pb: 4.6 },
      { ticker: "AVGO", pe: 33.6, ev: 24.4, pb: 12.1 },
      { ticker: "INTC", pe: 17.8, ev: 11.5, pb: 1.0 },
    ],
    sensitivity: sens(162),
    monteCarlo: mc(162, 55),
    risk: {
      level: "High",
      beta: 1.74,
      sharpe: 2.12,
      maxDrawdown: -56.2,
      var95: -5.1,
      altmanZ: 12.4,
      debtToEquity: 0.21,
      interestCoverage: 88.3,
      currentRatio: 4.11,
    },
    sentiment: {
      score: 86,
      yoyShift: 11.4,
      keywords: [
        { word: "Blackwell ramp", weight: 96, tone: "pos" },
        { word: "Sovereign AI", weight: 84, tone: "pos" },
        { word: "Customer concentration", weight: 73, tone: "neg" },
        { word: "Inference TAM", weight: 89, tone: "pos" },
        { word: "Export controls", weight: 67, tone: "neg" },
      ],
      redFlags: ["Top-4 hyperscaler concentration ~50% of revenue", "China export controls"],
    },
    memo: {
      summary: "NVIDIA is the dominant AI compute platform with a widening software moat (CUDA, NIM, Omniverse).",
      performance: "Data Center revenue >$30B/qtr at 75%+ gross margin; Blackwell ramp supply-constrained into FY26.",
      bear: 98,
      base: 162,
      bull: 215,
      risks: ["Hyperscaler in-house silicon", "Cyclical AI capex digestion", "Geopolitical/export risk"],
      thesis: "Inference becomes 60% of compute by FY27; CUDA software moat keeps share >80% — supports 17% upside.",
      bearCase: "AI capex digestion in FY26 + competitive in-house ASICs drive a -40% revenue reset to a $98 fair value.",
    },
  },
};

export const TICKERS = Object.keys(COMPANIES);

export const getCompany = (t: string) => COMPANIES[t.toUpperCase()];
