import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] });
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CatalystLens · News-to-Market Impact Research',
  description:
    'A self-hosted AI engineering system that extracts financial-news catalysts and measures the resulting market reaction.',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={geistSans.variable + ' ' + geistMono.variable}>{children}</body>
    </html>
  );
}
