import { Routes, Route } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { Overview } from './pages/Overview';
import { Workspace } from './pages/Workspace';
import { RunAssurance } from './pages/RunConfiguration';
import { RunProgress } from './pages/RunProgress';
import { Findings } from './pages/Findings';
import { Evidence } from './pages/Evidence';
import { DistributionShift } from './pages/DistributionShift';
import { Comparator } from './pages/Comparator';
import { Provenance } from './pages/Provenance';
import { Reports } from './pages/Reports';

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/workspace" element={<Workspace />} />
        <Route path="/run-assurance" element={<RunAssurance />} />
        <Route path="/run-progress" element={<RunProgress />} />
        <Route path="/findings" element={<Findings />} />
        <Route path="/evidence" element={<Evidence />} />
        <Route path="/distribution-shift" element={<DistributionShift />} />
        <Route path="/comparator" element={<Comparator />} />
        <Route path="/provenance" element={<Provenance />} />
        <Route path="/reports" element={<Reports />} />
      </Routes>
    </MainLayout>
  );
}

export default App;
