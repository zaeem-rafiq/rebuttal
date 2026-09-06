import CaseDetailsClient from './CaseDetailsClient';

export function generateStaticParams() {
  return [
    { id: 'dp_S1' },
    { id: 'dp_S2' },
    { id: 'dp_S3' },
    { id: 'du_1UCchuEmho7ai02fPo91XMwo' },
  ];
}

export default function CaseDetailsPage() {
  return <CaseDetailsClient />;
}
