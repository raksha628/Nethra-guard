const fs = require('fs');

const pages = [
  'Overview', 
  'Workspace', 
  'RunConfiguration', 
  'Findings', 
  'Evidence', 
  'Comparator', 
  'Provenance', 
  'Reports'
];

pages.forEach(p => {
  const componentName = p === 'RunConfiguration' ? 'RunAssurance' : p;
  const code = `export function ${componentName}() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">${p}</h2>
        <p className="text-sm text-ng-text-muted mt-1">Manage your ${p.toLowerCase()} here.</p>
      </div>
    </div>
  );
}
`;
  fs.writeFileSync(`src/pages/${p}/index.tsx`, code);
});
