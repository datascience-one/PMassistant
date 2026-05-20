import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderKanban, Sparkles, ArrowUpRight, Clock, FileText } from 'lucide-react'

export default function ProjectsPage() {
    const navigate = useNavigate()
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/projects')
            .then(r => r.json())
            .then(data => { setProjects(data.projects || []); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="w-10 h-10 border-3 border-primary-500/20 border-t-primary-500 rounded-full animate-spin" />
            </div>
        )
    }

    if (!projects.length) {
        return (
            <div className="empty-state animate-fade-in-up">
                <div className="empty-state-icon bg-gradient-to-br from-primary-500/10 to-accent-violet/10">
                    <FolderKanban className="w-9 h-9 text-primary-500" />
                </div>
                <h2 className="text-2xl font-black tracking-tight mb-2">No Projects Yet</h2>
                <p className="text-surface-500 text-sm mb-6 max-w-sm leading-relaxed">
                    Generate your first project to see it listed here.
                </p>
                <button
                    onClick={() => navigate('/')}
                    className="px-6 py-3 rounded-2xl bg-gradient-to-r from-primary-600 to-accent-violet text-white font-bold text-sm shadow-xl shadow-primary-500/20 hover:shadow-primary-500/35 transition-all"
                >
                    Create New Project
                </button>
            </div>
        )
    }

    return (
        <div className="page-container space-y-6">
            <div className="page-header animate-fade-in-up">
                <p className="page-subtitle">Workspace</p>
                <h1 className="page-title gradient-text">Projects</h1>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((p, i) => (
                    <div
                        key={p.name}
                        onClick={() => navigate(`/dashboard?project=${encodeURIComponent(p.name)}`)}
                        className="glass-card dash-card cursor-pointer group animate-fade-in-up"
                        style={{ animationDelay: `${i * 60}ms` }}
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br from-primary-500 to-accent-violet shadow-lg shadow-primary-500/15 group-hover:shadow-primary-500/30 transition-shadow">
                                <FileText className="w-5 h-5 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className="text-sm font-extrabold truncate group-hover:text-primary-500 transition-colors">{p.name}</h3>
                                <p className="text-[10px] text-surface-500 font-semibold uppercase tracking-wider">
                                    {p.files} files
                                </p>
                            </div>
                            <ArrowUpRight className="w-4 h-4 text-surface-500 opacity-0 group-hover:opacity-100 transition-all" />
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-surface-400 font-medium">
                            <Clock className="w-3 h-3" />
                            <span>{p.modified || 'Recent'}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
