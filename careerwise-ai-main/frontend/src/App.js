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
} from "recharts";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const fallbackSkills = [
  {
    skill: "Python",
    confidence: 0.93,
    section: "Projects",
    reasoning:
      "Found Python in 'Projects' section; verified via semantic context: 'Developed Django backend for skill analytics pipeline...'",
    box: { left: 21, top: 30, width: 34, height: 6 },
  },
  {
    skill: "React",
    confidence: 0.81,
    section: "Experience",
    reasoning:
      "Found React in 'Experience' section; verified via semantic context: 'Built interactive recruiter dashboards with React and hooks...'",
    box: { left: 18, top: 46, width: 28, height: 5 },
  },
];

const radarData = [
  { topic: "Python", candidate: 95, required: 90 },
  { topic: "FastAPI", candidate: 84, required: 85 },
  { topic: "React", candidate: 82, required: 80 },
  { topic: "NLP", candidate: 74, required: 88 },
  { topic: "SQL", candidate: 69, required: 75 },
];

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [numPages, setNumPages] = useState(1);

  const totalScore = useMemo(
    () => Math.round((fallbackSkills.reduce((s, sk) => s + sk.confidence, 0) / fallbackSkills.length) * 100),
    []
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl p-6 lg:p-10">
        <motion.h1
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-4xl font-bold tracking-tight"
        >
          SkillExtract AI · Spatial-Semantic Integrity Console
        </motion.h1>

        <div className="mb-6 flex flex-wrap items-center gap-4">
          <label className="rounded-2xl border border-white/20 bg-white/10 px-4 py-2 shadow-glass backdrop-blur-xl">
            <span className="mr-2 text-sm text-slate-300">Upload Resume PDF</span>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
              className="text-sm"
            />
          </label>
          <div className="rounded-2xl border border-white/20 bg-emerald-400/10 px-4 py-2 text-sm shadow-glass backdrop-blur-xl">
            Match Accuracy Gauge: <span className="font-semibold text-emerald-300">{totalScore}%</span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <section className="xl:col-span-2 rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl">
            <h2 className="mb-3 text-xl font-semibold">X-Ray Resume Viewer</h2>
            <div className="relative overflow-auto rounded-xl bg-slate-900 p-3">
              <Document
                file={pdfFile}
                onLoadSuccess={({ numPages: loaded }) => setNumPages(loaded)}
                loading={<p>Loading PDF...</p>}
                error={<p>No PDF loaded yet. Upload a resume to render overlays.</p>}
              >
                <div className="relative inline-block">
                  <Page pageNumber={1} width={760} />
                  {fallbackSkills.map((item) => {
                    const high = item.confidence >= 0.85;
                    return (
                      <div
                        key={item.skill}
                        title={`${item.skill}: ${(item.confidence * 100).toFixed(0)}%`}
                        className={`absolute rounded-md border ${
                          high
                            ? "border-emerald-400 bg-emerald-400/25"
                            : "border-yellow-300 bg-yellow-300/25"
                        }`}
                        style={{
                          left: `${item.box.left}%`,
                          top: `${item.box.top}%`,
                          width: `${item.box.width}%`,
                          height: `${item.box.height}%`,
                        }}
                      />
                    );
                  })}
                </div>
              </Document>
            </div>
            <p className="mt-2 text-xs text-slate-300">Pages detected: {numPages}</p>
          </section>

          <aside className="space-y-6">
            <div className="rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl">
              <h3 className="text-lg font-semibold">Verification Evidence</h3>
              <div className="mt-3 space-y-3">
                {fallbackSkills.map((item) => (
                  <div key={item.skill} className="rounded-xl border border-white/15 bg-slate-900/50 p-3">
                    <p className="font-medium">{item.skill}</p>
                    <p className="text-xs text-slate-300">{item.reasoning}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-xl">
              <h3 className="mb-4 text-lg font-semibold">Skill-Gap Radar</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart outerRadius="78%" data={radarData}>
                    <PolarGrid stroke="#6b7280" />
                    <PolarAngleAxis dataKey="topic" stroke="#e2e8f0" />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#94a3b8" />
                    <Radar
                      name="Candidate"
                      dataKey="candidate"
                      stroke="#34d399"
                      fill="#34d399"
                      fillOpacity={0.3}
                    />
                    <Radar name="Required" dataKey="required" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.22} />
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
