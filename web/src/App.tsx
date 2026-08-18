import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ChecklistPage } from './pages/ChecklistPage'
import { ColumnPage } from './pages/ColumnPage'
import { EnglishPage } from './pages/EnglishPage'
import { FeynmanPage } from './pages/FeynmanPage'
import { HomePage } from './pages/HomePage'
import { MockDetailPage, MocksPage } from './pages/MocksPage'
import { QuestionDetailPage } from './pages/QuestionDetailPage'
import { QuestionsPage } from './pages/QuestionsPage'
import { SimonPage } from './pages/SimonPage'
import { SpeakPage } from './pages/SpeakPage'
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
          <Route path="/practice/feynman" element={<FeynmanPage />} />
          <Route path="/practice/simon" element={<SimonPage />} />
          <Route path="/practice/speak" element={<SpeakPage />} />
          <Route path="/column/:columnKey" element={<ColumnPage />} />
          <Route path="/column/:columnKey/:docId" element={<ColumnPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
