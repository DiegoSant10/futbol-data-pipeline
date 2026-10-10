-- Test singular: devuelve las filas que INCUMPLEN la regla (el test pasa si no hay ninguna).
select *
from {{ ref('standings') }}
where points != 3 * won + drawn
   or played != won + drawn + lost
