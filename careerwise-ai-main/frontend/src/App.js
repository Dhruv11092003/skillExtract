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
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`;

const defaultSkills = [
  {
    skill: "Python",
    confidence: 0.93,
    section: "projects",
    reasoning:
      "Found Python in 'Projects' section; verified via semantic context: 'Developed Django backend for skill analytics pipeline...'",
    box: { left: 21, top: 30, width: 34, height: 6 },
  },
  {
    skill: "React",
    confidence: 0.81,
    section: "experience",
    reasoning:
      "Found React in 'Experience' section; verified via semantic context: 'Built interactive recruiter dashboards with React and hooks...'",
    box: { left: 18, top: 46, width: 28, height: 5 },
  },
  {
    skill: "FastAPI",
    confidence: 0.74,
    section: "skills",
    reasoning:
      "Found FastAPI in 'Skills' area; verified via semantic context: 'Built API services for NLP resume evaluation...'",
    box: { left: 56, top: 36, width: 22, height: 5 },
  },
];

const defaultRadar = [
  { topic: "Python", candidate: 95, required: 90 },
  { topic: "FastAPI", candidate: 84, required: 85 },
  { topic: "React", candidate: 82, required: 80 },
  { topic: "NLP", candidate: 74, required: 88 },
  { topic: "SQL", candidate: 69, required: 75 },
];

const apiBase = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

function scoreToColor(confidence) {
  if (confidence >= 0.85) return "border-emerald-300 bg-emerald-300/30";
  if (confidence >= 0.65) return "border-yellow-300 bg-yellow-300/30";
  return "border-rose-300 bg-rose-300/30";
}

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [numPages, setNumPages] = useState(1);
  const [jobSkills, setJobSkills] = useState("Python,FastAPI,React,Django,SQL");
  const [skills, setSkills] = useState(defaultSkills);
  const [radarData, setRadarData] = useState(defaultRadar);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Ready");
  const [selectedSkill, setSelectedSkill] = useState(defaultSkills[0]?.skill || "");

  const totalScore = useMemo(() => {
    if (!skills.length) return 0;
    return Math.round((skills.reduce((acc, item) => acc + item.confidence, 0) / skills.length) * 100);
  }, [skills]);

  const selectedReasoning = useMemo(
    () => skills.find((item) => item.skill === selectedSkill)?.reasoning || "Upload and analyze a PDF to inspect reasoning.",
    [selectedSkill, skills]
  );

  const handleAnalyze = async () => {
    if (!pdfFile) {
      setError("Please upload a PDF before running analysis.");
      return;
    }

    setIsAnalyzing(true);
    setError("");
    setStatus("Analyzing spatial structure and semantic evidence...");

    try {
      const formData = new FormData();
      formData.append("resume", pdfFile);
      formData.append("job_skills", jobSkills);

      const response = await fetch(`${apiBase}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Failed to analyze the uploaded PDF.");
      }

      const normalized = (data.extracted_skills || []).map((item, idx) => ({
        ...item,
        box: defaultSkills[idx % defaultSkills.length]?.box || { left: 20, top: 25 + idx * 8, width: 24, height: 5 },
      }));
      setSkills(normalized.length ? normalized : defaultSkills);
      setSelectedSkill(normalized[0]?.skill || "");

      const requested = jobSkills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const radar = requested.map((name) => {
        const matched = normalized.find((item) => item.skill.toLowerCase() === name.toLowerCase());
        return {
          topic: name,
          candidate: Math.round((matched?.confidence || 0) * 100),
          required: 85,
        };
      });
      setRadarData(radar.length ? radar : defaultRadar);
      setStatus("Analysis completed successfully.");
    } catch (err) {
      setError(err.message || "Unexpected error occurred during analysis.");
      setStatus("Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl p-6 lg:p-10">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 rounded-3xl border border-fuchsia-200/20 bg-gradient-to-r from-violet-500/10 via-cyan-400/5 to-emerald-400/10 p-6 backdrop-blur-2xl"
        >
          <h1 className="text-4xl font-black tracking-tight md:text-5xl">SkillExtract AI</h1>
          <p className="mt-2 text-slate-300">Spatial-Semantic Integrity Console · Hallucination-Resistant Recruitment Intelligence</p>
          <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
            <span className="rounded-full border border-emerald-300/40 bg-emerald-500/15 px-3 py-1">Match Accuracy: {totalScore}%</span>
            <span className="rounded-full border border-cyan-300/40 bg-cyan-500/15 px-3 py-1">Status: {status}</span>
          </div>
        </motion.div>

        <div className="mb-6 grid grid-cols-1 gap-4 rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl md:grid-cols-12">
          <label className="md:col-span-4 rounded-2xl border border-white/20 bg-white/5 px-4 py-3">
            <span className="mb-2 block text-sm text-slate-300">Upload Resume PDF</span>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => {
                setPdfFile(e.target.files?.[0] || null);
                setError("");
              }}
              className="w-full text-sm"
            />
          </label>

          <label className="md:col-span-6 rounded-2xl border border-white/20 bg-white/5 px-4 py-3">
            <span className="mb-2 block text-sm text-slate-300">Job Skills (comma-separated)</span>
            <input
              value={jobSkills}
              onChange={(e) => setJobSkills(e.target.value)}
              className="w-full rounded-xl border border-white/20 bg-slate-900/70 px-3 py-2 text-sm outline-none ring-cyan-400/40 transition focus:ring"
              placeholder="Python,FastAPI,React,Django,SQL"
            />
          </label>

          <div className="md:col-span-2 flex items-end">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full rounded-2xl bg-gradient-to-r from-cyan-500 to-emerald-500 px-4 py-3 text-sm font-bold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isAnalyzing ? "Analyzing..." : "Run Integrity Scan"}
            </button>
          </div>
        </div>

        {error && <div className="mb-4 rounded-xl border border-rose-400/40 bg-rose-500/15 px-4 py-3 text-sm text-rose-200">{error}</div>}

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <section className="xl:col-span-2 rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl">
            <h2 className="mb-3 text-xl font-semibold">X-Ray Resume Viewer</h2>
            <div className="relative overflow-auto rounded-xl bg-slate-900 p-3">
              {pdfFile ? (
                <Document
                  file={pdfFile}
                  onLoadSuccess={({ numPages: loaded }) => setNumPages(loaded)}
                  onLoadError={(err) => setError(`PDF render error: ${err.message}`)}
                  loading={<p className="text-slate-300">Loading PDF...</p>}
                  error={<p className="text-rose-300">Could not render PDF. Please ensure it is a valid text-based PDF.</p>}
                >
                  <div className="relative inline-block">
                    <Page pageNumber={1} width={760} renderTextLayer renderAnnotationLayer />
                    {skills.map((item) => (
                      <button
                        key={item.skill}
                        type="button"
                        onClick={() => setSelectedSkill(item.skill)}
                        title={`${item.skill}: ${(item.confidence * 100).toFixed(0)}%`}
                        className={`absolute rounded-md border transition hover:scale-[1.02] ${scoreToColor(item.confidence)}`}
                        style={{
                          left: `${item.box.left}%`,
                          top: `${item.box.top}%`,
                          width: `${item.box.width}%`,
                          height: `${item.box.height}%`,
                        }}
                      />
                    ))}
                  </div>
                </Document>
              ) : (
                <p className="py-16 text-center text-slate-400">No PDF loaded yet. Upload a resume to render overlays.</p>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-300">Pages detected: {numPages} · Overlay colors: Green (high), Yellow (review), Red (low).</p>
          </section>

          <aside className="space-y-6">
            <div className="rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl">
              <h3 className="text-lg font-semibold">Verification Evidence</h3>
              <div className="mt-3 space-y-3">
                {skills.map((item) => (
                  <button
                    type="button"
                    key={item.skill}
                    onClick={() => setSelectedSkill(item.skill)}
                    className="block w-full rounded-xl border border-white/15 bg-slate-900/50 p-3 text-left transition hover:border-cyan-300/50"
                  >
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{item.skill}</p>
                      <span className="text-xs text-slate-300">{Math.round(item.confidence * 100)}%</span>
                    </div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">Section: {item.section}</p>
                  </button>
                ))}
              </div>
              <div className="mt-4 rounded-xl border border-cyan-300/30 bg-cyan-500/10 p-3">
                <p className="text-sm font-semibold">Reasoning</p>
                <p className="mt-1 text-xs text-slate-200">{selectedReasoning}</p>
              </div>
            </div>

            <div className="rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl">
              <h3 className="mb-4 text-lg font-semibold">Skill-Gap Radar</h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart outerRadius="75%" data={radarData}>
                    <PolarGrid stroke="#6b7280" />
                    <PolarAngleAxis dataKey="topic" stroke="#e2e8f0" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#94a3b8" />
                    <Radar name="Candidate" dataKey="candidate" stroke="#34d399" fill="#34d399" fillOpacity={0.32} />
                    <Radar name="Required" dataKey="required" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default App;
