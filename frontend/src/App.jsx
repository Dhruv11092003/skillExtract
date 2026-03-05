import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Document, Page, pdfjs } from "react-pdf";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Upload, ShieldCheck, Radar as RadarIcon } from "lucide-react";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const defaultSkills = "Python,FastAPI,React,SQL,Django";

function radarFromSkills(skills) {
  const domains = [
    { topic: "Backend", keys: ["python", "fastapi", "django", "flask", "api"] },
    { topic: "Frontend", keys: ["react", "javascript", "typescript", "css", "html"] },
    { topic: "Data", keys: ["sql", "pandas", "numpy", "spark"] },
    { topic: "AI/NLP", keys: ["bert", "nlp", "transformer", "ml", "ai"] },
    { topic: "DevOps", keys: ["docker", "kubernetes", "aws", "ci", "cd"] },
  ];

  return domains.map((domain) => {
    const hits = skills.filter((skill) => domain.keys.some((k) => skill.skill.toLowerCase().includes(k))).length;
    return { topic: domain.topic, density: Math.min(100, hits * 25 + 10) };
  });
}

function overlayClass(score) {
  if (score >= 0.85) return "stroke-emerald-300 fill-emerald-300/25";
  if (score >= 0.65) return "stroke-yellow-300 fill-yellow-300/25";
  return "stroke-rose-300 fill-rose-300/25";
}

export default function App() {
  const [file, setFile] = useState(null);
  const [numPages, setNumPages] = useState(1);
  const [skillsInput, setSkillsInput] = useState(defaultSkills);
  const [skills, setSkills] = useState([]);
  const [selected, setSelected] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Upload a resume to start analysis.");

  const accuracy = useMemo(() => {
    if (!skills.length) return 0;
    return Math.round((skills.reduce((acc, s) => acc + s.confidence_score, 0) / skills.length) * 100);
  }, [skills]);

  const radarData = useMemo(() => radarFromSkills(skills), [skills]);

  async function analyze() {
    if (!file) {
      setError("Please upload a PDF resume first.");
      return;
    }

    setError("");
    setStatus("Running spatial-semantic verification...");
    setIsLoading(true);

    try {
      const body = new FormData();
      body.append("resume", file);
      body.append("job_skills", skillsInput);

      const response = await fetch(`${apiBaseUrl}/analyze`, { method: "POST", body });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed.");
      }

      const detected = data.skills || [];
      setSkills(detected);
      setSelected(detected[0] || null);
      setStatus(`Analysis complete. ${detected.length} skill(s) verified.`);
    } catch (err) {
      setError(err.message || "Unknown error");
      setStatus("Analysis failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen px-4 py-8 md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <motion.header
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-white/20 bg-white/10 p-6 shadow-glass backdrop-blur-2xl"
        >
          <h1 className="text-3xl font-black md:text-5xl">SkillExtract · High-Integrity Resume Intelligence</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-300 md:text-base">
            Spatial-semantic mapping engine that validates skill claims with PDF coordinates and contextual evidence.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge className="border-cyan-300/50 text-cyan-200">Accuracy: {accuracy}%</Badge>
            <Badge className="font-mono">{status}</Badge>
          </div>
        </motion.header>

        <Card className="grid gap-4 md:grid-cols-12">
          <label className="md:col-span-4">
            <span className="mb-2 flex items-center gap-2 text-sm text-slate-300"><Upload size={14} /> Resume PDF</span>
            <input
              type="file"
              accept="application/pdf"
              className="w-full rounded-xl border border-white/20 bg-slate-900/60 p-2 text-sm"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <label className="md:col-span-6">
            <span className="mb-2 flex items-center gap-2 text-sm text-slate-300"><ShieldCheck size={14} /> Required Skills</span>
            <input
              value={skillsInput}
              onChange={(event) => setSkillsInput(event.target.value)}
              className="w-full rounded-xl border border-white/20 bg-slate-900/60 p-2 text-sm font-mono"
            />
          </label>
          <div className="flex items-end md:col-span-2">
            <Button onClick={analyze} disabled={isLoading} className="w-full">
              {isLoading ? "Analyzing..." : "Analyze"}
            </Button>
          </div>
        </Card>

        {error && <Card className="border-rose-400/40 bg-rose-500/10 text-rose-100">{error}</Card>}

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <h2 className="mb-3 text-xl font-semibold">X-Ray PDF View</h2>
            <div className="overflow-auto rounded-xl bg-slate-900 p-3">
              {file ? (
                <Document
                  file={file}
                  onLoadSuccess={({ numPages: pages }) => setNumPages(pages)}
                  onLoadError={(err) => setError(`PDF render error: ${err.message}`)}
                  loading={<p className="text-sm text-slate-300">Loading PDF…</p>}
                >
                  <div className="relative inline-block">
                    <Page pageNumber={1} width={760} />
                    <svg className="absolute left-0 top-0 h-full w-full pointer-events-none" viewBox="0 0 760 1075" preserveAspectRatio="none">
                      {skills
                        .filter((item) => item.coordinates.page === 1)
                        .map((item) => {
                          const c = item.coordinates;
                          const x = (c.x0 / c.page_width) * 760;
                          const y = (c.y0 / c.page_height) * 1075;
                          const w = ((c.x1 - c.x0) / c.page_width) * 760;
                          const h = ((c.y1 - c.y0) / c.page_height) * 1075;
                          return (
                            <rect
                              key={`${item.skill}-${x}`}
                              x={x}
                              y={y}
                              width={Math.max(w, 12)}
                              height={Math.max(h, 12)}
                              className={overlayClass(item.confidence_score)}
                              strokeWidth="1.5"
                            />
                          );
                        })}
                    </svg>
                  </div>
                </Document>
              ) : (
                <p className="py-20 text-center text-slate-400">Upload a PDF to render X-Ray overlays.</p>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-400">Pages: {numPages}. Overlay = backend coordinate projections.</p>
          </Card>

          <div className="space-y-6">
            <Card>
              <h3 className="mb-3 text-lg font-semibold">Verification Evidence</h3>
              <motion.div
                className="space-y-2"
                initial="hidden"
                animate="visible"
                variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
              >
                {skills.length === 0 && <p className="text-sm text-slate-400">No verified skills yet.</p>}
                {skills.map((item) => (
                  <motion.button
                    key={`${item.skill}-${item.coordinates.x0}`}
                    variants={{ hidden: { opacity: 0, y: 6 }, visible: { opacity: 1, y: 0 } }}
                    onClick={() => setSelected(item)}
                    className="block w-full rounded-xl border border-white/20 bg-slate-900/60 p-3 text-left transition hover:border-cyan-300/60"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">{item.skill}</span>
                      <span className="font-mono text-xs">{Math.round(item.confidence_score * 100)}%</span>
                    </div>
                    <p className="text-xs uppercase tracking-wider text-slate-400">{item.section}</p>
                  </motion.button>
                ))}
              </motion.div>
              {selected && (
                <div className="mt-3 rounded-xl border border-cyan-300/30 bg-cyan-500/10 p-3 text-xs">
                  <p className="font-semibold">Evidence Snippet</p>
                  <p className="mt-1 text-slate-200">{selected.evidence_snippet}</p>
                </div>
              )}
            </Card>

            <Card>
              <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold"><RadarIcon size={16} /> Skill Density Radar</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData} outerRadius="75%">
                    <PolarGrid stroke="#64748b" />
                    <PolarAngleAxis dataKey="topic" stroke="#e2e8f0" />
                    <PolarRadiusAxis domain={[0, 100]} stroke="#94a3b8" />
                    <Radar dataKey="density" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.35} />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
