interface Props {
  isLegacy: boolean;
}

export default function BadgeLegacy({ isLegacy }: Props) {
  if (!isLegacy) return null;

  return (
    <span className="inline-flex items-center rounded-full border border-fuchsia-500 bg-fuchsia-500/20 px-3 py-1 text-xs font-bold text-fuchsia-200">
      CONTRATO LEGACY
    </span>
  );
}
