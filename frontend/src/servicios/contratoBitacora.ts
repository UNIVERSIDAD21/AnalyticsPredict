/** Contrato v2 de seguimiento: un fallo o un payload desconocido nunca es una lista vacía. */
export function leerDatosBitacora<T>(
  payload: unknown,
  campos: Record<string, 'number' | 'array' | 'object'>
): T {
  if (!payload || typeof payload !== 'object') {
    throw new Error('Respuesta de seguimiento inválida');
  }
  const envelope = payload as Record<string, unknown>;
  if (envelope.ok !== true || !envelope.data || typeof envelope.data !== 'object' || Array.isArray(envelope.data)) {
    throw new Error('La seguimiento no devolvió el contrato v2 esperado');
  }
  const data = envelope.data as Record<string, unknown>;
  for (const [campo, tipo] of Object.entries(campos)) {
    const valor = data[campo];
    const valido = tipo === 'array' ? Array.isArray(valor) : tipo === 'object'
      ? !!valor && typeof valor === 'object' && !Array.isArray(valor)
      : typeof valor === 'number' && Number.isFinite(valor);
    if (!valido) throw new Error(`Contrato de seguimiento inválido: ${campo}`);
  }
  return data as T;
}
