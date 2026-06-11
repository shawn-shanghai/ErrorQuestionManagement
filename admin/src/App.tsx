import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import QuestionsPage from './pages/QuestionsPage'
import SubjectsPage from './pages/SubjectsPage'
import TagsPage from './pages/TagsPage'
import './App.css'

export default function App() {
  return (
    <Router>
      <div className="admin-container">
        <nav className="admin-nav">
          <h1>ExamCenter Admin</h1>
          <ul>
            <li><a href="/admin/questions">Questions</a></li>
            <li><a href="/admin/subjects">Subjects</a></li>
            <li><a href="/admin/tags">Tags</a></li>
          </ul>
        </nav>
        <main className="admin-main">
          <Routes>
            <Route path="/" element={<Navigate to="/admin/questions" replace />} />
            <Route path="/questions" element={<QuestionsPage />} />
            <Route path="/subjects" element={<SubjectsPage />} />
            <Route path="/tags" element={<TagsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}
