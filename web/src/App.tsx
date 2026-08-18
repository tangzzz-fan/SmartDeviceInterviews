import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ChecklistPage } from './pages/ChecklistPage'
import { EnglishPage } from './pages/EnglishPage'
import { HomePage } from './pages/HomePage'
import { MockDetailPage, MocksPage } from './pages/MocksPage'
import { QuestionDetailPage } from './pages/QuestionDetailPage'
import { QuestionsPage } from './pages/QuestionsPage'
import { SkillsPage } from './pages/SkillsPage'
import { StoriesPage } from './pages/StoriesPage'
import { WhiteboardsPage } from './pages/WhiteboardsPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/questions" element={<QuestionsPage />} />
          <Route path="/questions/:id" element={<QuestionDetailPage />} />
          <Route path="/checklist" element={<ChecklistPage />} />
          <Route path="/whiteboards" element={<WhiteboardsPage />} />
          <Route path="/stories" element={<StoriesPage />} />
          <Route path="/english" element={<EnglishPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/mocks" element={<MocksPage />} />
          <Route path="/mocks/:id" element={<MockDetailPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
