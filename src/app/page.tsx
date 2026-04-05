"use client";

import { useEffect, useState } from "react";

const tools = [
  { name: "Claude Code", description: "AI coding assistant trong terminal", category: "AI Assistant" },
  { name: "Cursor", description: "AI-powered code editor", category: "IDE" },
  { name: "Next.js", description: "React framework cho production", category: "Framework" },
  { name: "Tailwind CSS", description: "Utility-first CSS framework", category: "Styling" },
  { name: "Vercel", description: "Platform deploy & hosting", category: "Deployment" },
  { name: "GitHub", description: "Source control & collaboration", category: "DevOps" },
  { name: "TypeScript", description: "JavaScript voi type safety", category: "Language" },
  { name: "Figma", description: "Design & prototyping tool", category: "Design" },
];

function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
    </svg>
  );
}

export default function Home() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggleDark() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors duration-300">
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 dark:bg-gray-950/80 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">T</div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">ThiemAICamp</span>
          </div>
          <button onClick={toggleDark} className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-300" aria-label="Toggle dark mode">
            {dark ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 pt-24 pb-16">
        <div className="max-w-3xl">
          <div className="inline-block px-4 py-1.5 rounded-full bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 text-sm font-medium mb-6">AI Software Office</div>
          <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 dark:text-white leading-tight mb-6">
            Xay dung san pham<br />
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">voi suc manh AI</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 leading-relaxed mb-10 max-w-2xl">
            ThiemAICamp la van phong phan mem AI - noi chung toi ket hop con nguoi va tri tue nhan tao de tao ra nhung san pham cong nghe chat luong, nhanh chong va hieu qua.
          </p>
          <div className="flex flex-wrap gap-4">
            <a href="#tools" className="px-8 py-3.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:opacity-90 transition-opacity">Kham pha Tools</a>
            <a href="#about" className="px-8 py-3.5 rounded-full border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">Tim hieu them</a>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { value: "10x", label: "Nang suat tang" },
            { value: "AI-First", label: "Phuong phap" },
            { value: tools.length + "+", label: "AI Tools" },
            { value: "24/7", label: "AI ho tro" },
          ].map((stat) => (
            <div key={stat.label} className="text-center p-6 rounded-2xl bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800">
              <div className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">{stat.value}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="tools" className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">Tools & Stack</h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Bo cong cu AI-powered ma chung toi su dung hang ngay de xay dung san pham</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {tools.map((tool) => (
            <div key={tool.name} className="group p-6 rounded-2xl bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-lg hover:shadow-blue-500/5 transition-all duration-300">
              <div className="text-xs font-medium text-blue-500 dark:text-blue-400 uppercase tracking-wider mb-2">{tool.category}</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">{tool.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{tool.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="about" className="max-w-6xl mx-auto px-6 py-16">
        <div className="rounded-3xl bg-gradient-to-br from-blue-500 to-purple-600 p-10 sm:p-16 text-white">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">Ve ThiemAICamp</h2>
          <div className="grid sm:grid-cols-2 gap-8 text-blue-100">
            <p className="leading-relaxed">Chung toi tin rang AI khong thay the con nguoi, ma giup con nguoi lam viec hieu qua hon. Tai ThiemAICamp, moi quy trinh deu duoc toi uu voi AI - tu viet code, thiet ke, den trien khai san pham.</p>
            <p className="leading-relaxed">Voi doi ngu am hieu ca cong nghe lan AI, chung toi mang den giai phap phan mem nhanh hon, thong minh hon, va tiet kiem chi phi hon cho doanh nghiep.</p>
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-200 dark:border-gray-800 mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">&copy; 2025 ThiemAICamp. All rights reserved.</div>
          <div className="flex gap-6 text-sm text-gray-500 dark:text-gray-400">
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">GitHub</a>
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Facebook</a>
            <a href="#" className="hover:text-gray-900 dark:hover:text-white transition-colors">Lien he</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
