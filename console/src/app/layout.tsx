import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
});

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
    <html lang="en" className={`dark ${plusJakarta.variable}`}>
      <body className="bg-[#0b0f17] text-[#f9fafb] font-sans antialiased selection:bg-blue-500/20 selection:text-white">
        <div className="relative min-h-screen flex flex-col">
          <main className="relative flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
