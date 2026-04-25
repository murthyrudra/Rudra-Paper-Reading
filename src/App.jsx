import { useState, useEffect, useMemo } from "react";

const ALL_TAGS = [
  "LLMs","RAG","Agents","Reasoning","Fine-tuning","NLP","Evaluation",
  "Multimodal","Alignment","RLHF","Prompting","Retrieval",
  "Efficient Training","Datasets","Interpretability","Code Generation",
  "Speech","Vision-Language","Knowledge Graphs","Reinforcement Learning"
];

const SOURCE_COLORS = {
  "arXiv":            { bg: "#EAF3DE", text: "#3B6D11" },
  "Semantic Scholar": { bg: "#E6F1FB", text: "#185FA5" },
};

function TagPill({ tag, active, onClick }) {
  return (
    <button
      onClick={() => onClick(tag)}
      style={{
        fontSize: 12,
        padding: "4px 11px",
        borderRadius: 99,
        border: active ? "none" : "1px solid #d0cfc8",
        background: active ? "#1a1a1a" : "transparent",
        color: active ? "#fff" : "#666",
        cursor: "pointer",
        fontFamily: "inherit",
        transition: "all .15s",
        whiteSpace: "nowrap",
      }}
    >
      {tag}
    </button>
  );
}

function PaperCard({ paper }) {
  const [expanded, setExpanded] = useState(false);
  const src = SOURCE_COLORS[paper.source] || { bg: "#F1EFE8", text: "#5F5E5A" };

  return (
    <div
      onClick={() => setExpanded(e => !e)}
      style={{
        background: "#fff",
        border: "1px solid #e8e6e0",
        borderRadius: 12,
        padding: "18px 20px",
        cursor: "pointer",
        transition: "border-color .15s, box-shadow .15s",
        marginBottom: 10,
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = "#bbb"}
      onMouseLeave={e => e.currentTarget.style.borderColor = "#e8e6e0"}
    >
      {/* Top row */}
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginBottom: 6 }}>
            <span style={{
              fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 99,
              background: src.bg, color: src.text,
            }}>
              {paper.source}
            </span>
            <span style={{ fontSize: 12, color: "#999" }}>{paper.date}</span>
          </div>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: "#111", lineHeight: 1.45, margin: 0 }}>
            {paper.title}
          </h3>
          {paper.authors?.length > 0 && (
            <p style={{ fontSize: 12, color: "#888", margin: "5px 0 0" }}>
              {paper.authors.slice(0,3).join(", ")}{paper.authors.length > 3 ? " et al." : ""}
            </p>
          )}
        </div>
        <span style={{ fontSize: 18, color: "#aaa", flexShrink: 0, marginTop: 2 }}>
          {expanded ? "−" : "+"}
        </span>
      </div>

      {/* Tags */}
      {paper.tags?.length > 0 && (
        <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginTop: 10 }}>
          {paper.tags.map(t => (
            <span key={t} style={{
              fontSize: 11, padding: "2px 8px", borderRadius: 4,
              background: "#f0ede6", color: "#555",
            }}>{t}</span>
          ))}
        </div>
      )}

      {/* Expanded content */}
      {expanded && (
        <div style={{ marginTop: 14, borderTop: "1px solid #f0ede6", paddingTop: 12 }}>
          {paper.summary && (
            <p style={{ fontSize: 13.5, color: "#444", lineHeight: 1.7, margin: "0 0 12px" }}>
              {paper.summary}
            </p>
          )}
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            style={{
              fontSize: 13, color: "#185FA5", textDecoration: "none",
              fontWeight: 500, display: "inline-flex", alignItems: "center", gap: 4,
            }}
          >
            View paper ↗
          </a>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [search, setSearch]     = useState("");
  const [activeTags, setActiveTags] = useState([]);
  const [sortBy, setSortBy]     = useState("date");
  const [showAllTags, setShowAllTags] = useState(false);

  useEffect(() => {
    fetch("/papers.json")
      .then(r => { if (!r.ok) throw new Error("Failed to load papers.json"); return r.json(); })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const toggleTag = tag => {
    setActiveTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const filtered = useMemo(() => {
    if (!data?.papers) return [];
    let papers = data.papers;

    if (search.trim()) {
      const q = search.toLowerCase();
      papers = papers.filter(p =>
        p.title?.toLowerCase().includes(q) ||
        p.summary?.toLowerCase().includes(q) ||
        p.authors?.some(a => a.toLowerCase().includes(q))
      );
    }

    if (activeTags.length > 0) {
      papers = papers.filter(p =>
        activeTags.every(t => p.tags?.includes(t))
      );
    }

    if (sortBy === "date") {
      papers = [...papers].sort((a,b) => (b.date||"").localeCompare(a.date||""));
    }

    return papers;
  }, [data, search, activeTags, sortBy]);

  // Tag frequency for ordering
  const tagCounts = useMemo(() => {
    if (!data?.papers) return {};
    const counts = {};
    data.papers.forEach(p => p.tags?.forEach(t => { counts[t] = (counts[t]||0)+1; }));
    return counts;
  }, [data]);

  const sortedTags = [...ALL_TAGS].sort((a,b) => (tagCounts[b]||0) - (tagCounts[a]||0));
  const visibleTags = showAllTags ? sortedTags : sortedTags.slice(0, 10);

  const lastUpdated = data?.last_updated
    ? new Date(data.last_updated).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })
    : null;

  return (
    <div style={{ minHeight: "100vh", background: "#f7f5f0", fontFamily: "'Georgia', serif" }}>

      {/* Header */}
      <div style={{
        background: "#111", color: "#fff",
        padding: "32px 24px 28px",
      }}>
        <div style={{ maxWidth: 760, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
            <div>
              <h1 style={{ fontSize: 26, fontWeight: 700, margin: 0, letterSpacing: "-0.5px" }}>
                Research Radar
              </h1>
              <p style={{ fontSize: 13, color: "#999", margin: "4px 0 0", fontFamily: "sans-serif" }}>
                Daily NLP &amp; LLM papers · arXiv · Semantic Scholar
              </p>
            </div>
            {lastUpdated && (
              <span style={{ fontSize: 12, color: "#666", fontFamily: "sans-serif", marginTop: 4 }}>
                Updated {lastUpdated}
              </span>
            )}
          </div>

          {/* Stats */}
          {data && (
            <div style={{ display: "flex", gap: 24, marginTop: 20, fontFamily: "sans-serif" }}>
              {[
                ["Total papers", data.total],
                ["Showing", filtered.length],
                ["Sources", "arXiv + S2"],
              ].map(([label, val]) => (
                <div key={label}>
                  <div style={{ fontSize: 20, fontWeight: 600, color: "#fff" }}>{val}</div>
                  <div style={{ fontSize: 11, color: "#777", marginTop: 1 }}>{label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Search + filters */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e8e6e0", padding: "16px 24px" }}>
        <div style={{ maxWidth: 760, margin: "0 auto" }}>
          <input
            type="search"
            placeholder="Search titles, summaries, authors…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: "100%", padding: "10px 14px", fontSize: 14,
              border: "1px solid #ddd", borderRadius: 8,
              fontFamily: "sans-serif", outline: "none",
              background: "#fafaf8", boxSizing: "border-box",
            }}
          />

          <div style={{ marginTop: 12, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "#999", fontFamily: "sans-serif", marginRight: 4 }}>Filter:</span>
            {visibleTags.map(tag => (
              <TagPill
                key={tag}
                tag={tag}
                active={activeTags.includes(tag)}
                onClick={toggleTag}
              />
            ))}
            <button
              onClick={() => setShowAllTags(v => !v)}
              style={{
                fontSize: 12, color: "#888", background: "none", border: "none",
                cursor: "pointer", fontFamily: "sans-serif", padding: "4px 6px",
              }}
            >
              {showAllTags ? "Less ↑" : `+${ALL_TAGS.length - 10} more`}
            </button>
            {activeTags.length > 0 && (
              <button
                onClick={() => setActiveTags([])}
                style={{
                  fontSize: 12, color: "#c0392b", background: "none", border: "none",
                  cursor: "pointer", fontFamily: "sans-serif", padding: "4px 6px", marginLeft: 4,
                }}
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Paper list */}
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "20px 24px 48px" }}>
        {loading && (
          <div style={{ textAlign: "center", padding: "60px 0", color: "#999", fontFamily: "sans-serif" }}>
            Loading papers…
          </div>
        )}
        {error && (
          <div style={{ textAlign: "center", padding: "60px 0", color: "#c0392b", fontFamily: "sans-serif" }}>
            <p style={{ fontWeight: 600 }}>Could not load papers</p>
            <p style={{ fontSize: 13, marginTop: 8 }}>{error}</p>
            <p style={{ fontSize: 13, color: "#999", marginTop: 8 }}>
              If this is a fresh deploy, run the GitHub Action manually to generate papers.json first.
            </p>
          </div>
        )}
        {!loading && !error && filtered.length === 0 && (
          <div style={{ textAlign: "center", padding: "60px 0", color: "#999", fontFamily: "sans-serif" }}>
            No papers match your filters.
          </div>
        )}
        {filtered.map(paper => (
          <PaperCard key={paper.id} paper={paper} />
        ))}
      </div>
    </div>
  );
}
