import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "@/components/ui/header";
import Footer from "@/components/ui/footer";
import Home from "./pages/Home";
import DailySchedule from "./pages/DailySchedule";
import GriefGuide from "./pages/GriefGuide";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () =>
<QueryClientProvider client={queryClient} data-id="siiwh4jm6" data-path="src/App.tsx">
    <TooltipProvider data-id="2ljwlsl13" data-path="src/App.tsx">
      <Toaster data-id="usn34tz9b" data-path="src/App.tsx" />
      <BrowserRouter data-id="qiohz2qdv" data-path="src/App.tsx">
        <div className="min-h-screen flex flex-col" data-id="ru8yccsaq" data-path="src/App.tsx">
          <Header data-id="g9afxz09r" data-path="src/App.tsx" />
          <main className="flex-1" data-id="lkhe8sloq" data-path="src/App.tsx">
            <Routes data-id="ikrz21xl0" data-path="src/App.tsx">
              <Route path="/" element={<Home data-id="0ruo3cx5e" data-path="src/App.tsx" />} data-id="ev7tfllng" data-path="src/App.tsx" />
              <Route path="/daily-schedule" element={<DailySchedule data-id="gplw2av3n" data-path="src/App.tsx" />} data-id="2nmdveet0" data-path="src/App.tsx" />
              <Route path="/grief-guide" element={<GriefGuide data-id="2aq5byw7q" data-path="src/App.tsx" />} data-id="fc6jcha7a" data-path="src/App.tsx" />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound data-id="oaklh9od4" data-path="src/App.tsx" />} data-id="30yor90ne" data-path="src/App.tsx" />
            </Routes>
          </main>
          <Footer data-id="mw3i17s5b" data-path="src/App.tsx" />
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>;



export default App;