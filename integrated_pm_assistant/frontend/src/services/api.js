import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export async function startProject(payload) {
    const { data } = await api.post('/start-project', payload)
    return data
}

export async function uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/upload-file', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    })
    return data
}

export async function pollJobStatus(jobId) {
    const { data } = await api.get(`/job-status/${jobId}`)
    return data
}

export async function getProjectResults(projectName) {
    const { data } = await api.get(`/project-results/${encodeURIComponent(projectName)}`)
    return data
}

export function getDownloadUrl(filename) {
    return `/api/download/${encodeURIComponent(filename)}`
}

export async function syncMeetings(projectName, meetingType) {
    const { data } = await api.post('/sync-meetings', {
        project_name: projectName,
        meeting_type: meetingType
    })
    return data
}

export async function getProjects() {
    const { data } = await api.get('/projects')
    return data
}

