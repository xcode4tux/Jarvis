import { useEffect, useState } from 'react';
import {
  Compass,
  Cpu,
  Trash2,
  RefreshCw,
  Plus,
  Search,
  BookOpen,
  Settings,
  Layers,
  ArrowRight,
  ShieldAlert,
  FolderSync,
  Tag,
  CheckCircle,
  AlertCircle,
  Power
} from 'lucide-react';
import { fetchSkills, removeSkill, syncSkills, enableSkill, disableSkill, type SkillInfo } from '../lib/api';
import { toast } from 'sonner';

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncSource, setSyncSource] = useState('hermes');
  const [syncCategory, setSyncCategory] = useState('');
  const [syncSearch, setSyncSearch] = useState('');
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);

  const loadSkills = async () => {
    setLoading(true);
    try {
      const data = await fetchSkills();
      setSkills(data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load skills');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSkills();
  }, []);

  const handleDelete = async (name: string) => {
    if (!confirm(`Are you sure you want to delete the skill "${name}"?`)) return;
    try {
      await removeSkill(name);
      toast.success(`Skill "${name}" deleted successfully`);
      loadSkills();
    } catch (error) {
      console.error(error);
      toast.error(`Failed to delete skill "${name}"`);
    }
  };

  const handleToggleEnable = async (name: string, currentEnabled: boolean) => {
    try {
      if (currentEnabled) {
        await disableSkill(name);
        toast.success(`Skill "${name}" disabled successfully`);
      } else {
        await enableSkill(name);
        toast.success(`Skill "${name}" enabled successfully`);
      }
      loadSkills();
    } catch (error) {
      console.error(error);
      toast.error(`Failed to ${currentEnabled ? 'disable' : 'enable'} skill "${name}"`);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await syncSkills({
        source: syncSource,
        category: syncCategory || undefined,
        search: syncSearch || undefined,
        force: true
      });
      toast.success(`Successfully synced! Imported ${result.imported} skill(s).`);
      loadSkills();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.message || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const filteredSkills = skills.filter((skill) => {
    const query = searchQuery.toLowerCase();
    return (
      skill.name.toLowerCase().includes(query) ||
      (skill.description && skill.description.toLowerCase().includes(query)) ||
      skill.tags.some((tag) => tag.toLowerCase().includes(query))
    );
  });

  return (
    <div className="flex-1 flex flex-col overflow-hidden px-6 py-8 h-full">
      <div className="max-w-6xl mx-auto w-full flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <header className="mb-6 shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2" style={{ color: 'var(--color-text)' }} id="skills-title">
              <Layers className="text-indigo-500" size={24} />
              OpenJarvis Skills
            </h1>
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Procedural skills extend agent capabilities with multi-turn tool-calling pipelines and custom instructions.
            </p>
          </div>
          <button
            onClick={loadSkills}
            disabled={loading || syncing}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer self-start md:self-auto"
            style={{
              background: 'var(--color-bg-secondary)',
              color: 'var(--color-text-secondary)',
              border: '1px solid var(--color-border)',
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </header>

        {/* Sync Panel & Search bar */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6 shrink-0">
          {/* Sync form */}
          <div
            className="lg:col-span-2 rounded-xl p-4 flex flex-col justify-between gap-4"
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
              <FolderSync size={16} className="text-indigo-400" />
              <span>Import Hermes & Third-Party Skills</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[10px] uppercase font-bold block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Source Registry
                </label>
                <select
                  value={syncSource}
                  onChange={(e) => setSyncSource(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-xs outline-none cursor-pointer"
                  style={{
                    background: 'var(--color-bg-secondary)',
                    color: 'var(--color-text)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  <option value="hermes">Hermes Agent Repository</option>
                  <option value="openclaw">OpenClaw Registry</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] uppercase font-bold block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Category (optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. coding, research"
                  value={syncCategory}
                  onChange={(e) => setSyncCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-xs outline-none"
                  style={{
                    background: 'var(--color-bg-secondary)',
                    color: 'var(--color-text)',
                    border: '1px solid var(--color-border)',
                  }}
                />
              </div>
              <div>
                <label className="text-[10px] uppercase font-bold block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Keyword Search
                </label>
                <input
                  type="text"
                  placeholder="e.g. notes, pdf"
                  value={syncSearch}
                  onChange={(e) => setSyncSearch(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-xs outline-none"
                  style={{
                    background: 'var(--color-bg-secondary)',
                    color: 'var(--color-text)',
                    border: '1px solid var(--color-border)',
                  }}
                />
              </div>
            </div>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              style={{
                background: 'var(--color-accent)',
                color: '#fff',
                opacity: syncing ? 0.7 : 1,
              }}
            >
              <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing and Installing Skills...' : 'Sync & Import Selected Skills'}
            </button>
          </div>

          {/* Search tool */}
          <div
            className="rounded-xl p-4 flex flex-col justify-between"
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div className="flex items-center gap-2 text-sm font-semibold mb-2" style={{ color: 'var(--color-text)' }}>
              <Search size={16} style={{ color: 'var(--color-text-secondary)' }} />
              <span>Search Catalog</span>
            </div>
            <p className="text-xs mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
              Filter by name, description, tags, or capabilities.
            </p>
            <div
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
              }}
            >
              <Search size={14} style={{ color: 'var(--color-text-tertiary)' }} />
              <input
                type="text"
                placeholder="Type query..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent outline-none"
                style={{ color: 'var(--color-text)' }}
              />
            </div>
          </div>
        </div>

        {/* Skills list container */}
        <div className="flex-1 overflow-y-auto min-h-0 pr-1">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <RefreshCw className="animate-spin text-indigo-500 mb-4" size={32} />
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                Loading installed OpenJarvis skills...
              </p>
            </div>
          ) : filteredSkills.length === 0 ? (
            <div
              className="text-center py-16 px-4 rounded-xl border border-dashed flex flex-col items-center justify-center"
              style={{
                background: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
              }}
            >
              <AlertCircle size={40} className="text-indigo-400 mb-4" />
              <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--color-text)' }}>
                No Skills Found
              </h3>
              <p className="text-xs max-w-sm mb-6" style={{ color: 'var(--color-text-secondary)' }}>
                {searchQuery
                  ? 'No installed skills match your search query.'
                  : 'Get started by syncing the NousResearch Hermes Agent repository to load pre-built skills.'}
              </p>
              {!searchQuery && (
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                  style={{
                    background: 'var(--color-accent)',
                    color: '#fff',
                  }}
                >
                  <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
                  Import Starter Hermes Skills
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredSkills.map((skill) => {
                const isExpanded = expandedSkill === skill.name;
                return (
                  <div
                    key={skill.name}
                    className="rounded-xl p-5 flex flex-col justify-between transition-all"
                    style={{
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                    }}
                  >
                    <div>
                      {/* Name & Actions */}
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <h3 className="text-base font-bold flex items-center gap-2" style={{ color: 'var(--color-text)' }}>
                            {skill.name}
                          </h3>
                          <span className="text-[10px] font-medium block mt-0.5" style={{ color: 'var(--color-text-tertiary)' }}>
                            Version {skill.version} {skill.author ? `by ${skill.author}` : ''}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() => handleToggleEnable(skill.name, skill.enabled)}
                            className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                              skill.enabled
                                ? 'hover:bg-amber-500/10 hover:text-amber-500 text-slate-400'
                                : 'hover:bg-emerald-500/10 hover:text-emerald-500 text-emerald-500'
                            }`}
                            title={skill.enabled ? 'Disable Skill' : 'Enable Skill'}
                          >
                            <Power size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(skill.name)}
                            className="p-1.5 rounded-md hover:bg-red-500/10 hover:text-red-500 transition-colors text-slate-400 cursor-pointer"
                            title="Delete Skill"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-xs mb-3 leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                        {skill.description}
                      </p>

                      {/* Badges/Tags */}
                      <div className="flex flex-wrap gap-1.5 mb-4">
                        {/* Status Badge */}
                        <span
                          className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase flex items-center gap-1"
                          style={{
                            background: skill.enabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: skill.enabled ? 'rgb(52, 211, 153)' : 'rgb(248, 113, 113)',
                          }}
                        >
                          {skill.enabled ? (
                            <>
                              <CheckCircle size={8} />
                              Enabled
                            </>
                          ) : (
                            <>
                              <AlertCircle size={8} />
                              Disabled
                            </>
                          )}
                        </span>

                        {/* Type Badge */}
                        <span
                          className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase"
                          style={{
                            background: skill.has_instructions ? 'rgba(79, 70, 229, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: skill.has_instructions ? 'rgb(129, 140, 248)' : 'rgb(52, 211, 153)',
                          }}
                        >
                          {skill.has_instructions ? 'Instructional' : 'Pipeline'}
                        </span>

                        {/* Config Vis Badge */}
                        {skill.disable_model_invocation && (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-yellow-500/15 text-yellow-400">
                            Hidden from LLM
                          </span>
                        )}

                        {/* Standard tags */}
                        {skill.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-[9px] font-medium px-2 py-0.5 rounded-full flex items-center gap-1"
                            style={{
                              background: 'var(--color-bg-secondary)',
                              color: 'var(--color-text-secondary)',
                            }}
                          >
                            <Tag size={8} />
                            {tag}
                          </span>
                        ))}
                      </div>

                      {/* Capabilities */}
                      {skill.required_capabilities.length > 0 && (
                        <div className="mb-4">
                          <span className="text-[10px] font-semibold block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                            Required Capabilities
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {skill.required_capabilities.map((cap) => (
                              <span
                                key={cap}
                                className="text-[9px] px-1.5 py-0.5 rounded font-mono border"
                                style={{
                                  background: cap.includes('execute') ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                                  color: cap.includes('execute') ? 'var(--color-error)' : 'var(--color-text-secondary)',
                                  borderColor: cap.includes('execute') ? 'rgba(239, 68, 68, 0.2)' : 'var(--color-border)',
                                }}
                              >
                                {cap}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Steps pipeline preview */}
                      {skill.steps.length > 0 && (
                        <div className="mt-3">
                          <button
                            onClick={() => setExpandedSkill(isExpanded ? null : skill.name)}
                            className="text-[10px] font-bold flex items-center gap-1 hover:underline cursor-pointer"
                            style={{ color: 'var(--color-accent)' }}
                          >
                            {isExpanded ? 'Hide' : 'Show'} Pipeline Steps ({skill.steps.length})
                          </button>
                          {isExpanded && (
                            <div
                              className="mt-2 rounded-lg p-2.5 font-mono text-[10px] flex flex-col gap-2"
                              style={{
                                background: 'var(--color-bg-secondary)',
                                border: '1px solid var(--color-border)',
                              }}
                            >
                              {skill.steps.map((step, idx) => (
                                <div key={idx} className="flex items-start gap-1.5">
                                  <span style={{ color: 'var(--color-text-tertiary)' }}>{idx + 1}.</span>
                                  <div>
                                    <div className="font-semibold" style={{ color: 'var(--color-text)' }}>
                                      {step.tool_name ? `Tool: ${step.tool_name}` : `Skill: ${step.skill_name}`}
                                    </div>
                                    {step.output_key && (
                                      <div className="text-[9px] mt-0.5 text-indigo-400">
                                        Outputs to: {step.output_key}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
