/** Contrato v2 de bitácora: un fallo o un payload desconocido nunca es una lista vacía. */
export function leerDatosBitacora<T>(
  payload: unknown,
  campos: Record<string, 'number' | 'array' | 'object'>
): T {
  if (!payload || typeof payload !== 'object') {
    throw new Error('Respuesta de bitácora inválida');
  }
  const envelope = payload as Record<string, unknown>;
  if (envelope.ok !== true || !envelope.data || typeof envelope.data !== 'object' || Array.isArray(envelope.data)) {
    throw new Error('La bitácora no devolvió el contrato v2 esperado');
  }
  const data = envelope.data as Record<string, unknown>;
  for (const [campo, tipo] of Object.entries(campos)) {
    const valor = data[campo];
    const valido = tipo === 'array' ? Array.isArray(valor) : tipo === 'object'
      ? !!valor && typeof valor === 'object' && !Array.isArray(valor)
      : typeof valor === 'number' && Number.isFinite(valor);
    if (!valido) throw new Error(`Contrato de bitácora inválido: ${campo}`);
  }
  return data as T;
}
