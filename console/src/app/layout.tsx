import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Rebuttal · Autonomous Chargeback Defense',
  description: 'Autonomous chargeback-defense agent for small Stripe merchants powered by Bedrock AgentCore and AWS Strands',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased">
        <div className="relative min-h-screen flex flex-col">
          <main className="relative flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
