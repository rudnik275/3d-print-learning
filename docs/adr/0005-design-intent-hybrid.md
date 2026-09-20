# ADR-0005 — Тип документа Fusion по умолчанию: Hybrid, не Part

Дата: 2026-09-20. Статус: принято.

## Контекст

Fusion 2705 работает по модели Parts & Assemblies: у документа есть **design intent** — `Part`, `Assembly` или `Hybrid` (`Design.designIntent`, значения 0/1/2). Выключателя у модели нет: в настройках API ничего похожего, в `NGlobalOptions.xml` только `NotifyPartAssemblyWorkflow` — флаг уведомления, не переключатель поведения. Настройки «тип нового документа по умолчанию» в конфиге тоже нет.

Разница, проверенная в работающем Fusion 20.09 через `tools/fmcp.py`:

| Тип | Тела в корне | Дочерние компоненты |
| --- | --- | --- |
| Part | да | **запрещены** |
| Assembly | опционально (`isModelingInAssemblyEnabled`) | да |
| Hybrid | да | да |

Hybrid — это поведение Fusion до 2026: тела и компоненты уживаются в одном документе.

Поймали на живом: документ `kindle` создан как **Part**, и Snap Generator падал на любой своей команде с

```
RuntimeError: 3 : Failed to create component: Part Design documents can only contain one component
```

Аддин всегда создаёт компонент `snap_mechanism` (`lib/snaplib/geometry.py:68`, `occurrences.addNewComponent`), а настройку «не создавать компонент» автор убрал в 0.4.0 (issue #19, «this setting is pointless») — со стороны аддина не лечится. Так же сломается любой аддин, который создаёт компонент, а таких большинство: они писались до 2026, когда ограничения не существовало.

Воспроизведено на чистом документе, одна переменная — `designIntent`:

- `documents.add()` → intent = **Hybrid**, тело в корне и `addNewComponent` работают оба;
- тот же документ, `designIntent = Part` → `addNewComponent` блокируется ровно той же ошибкой;
- обратно `designIntent = Hybrid` → снова работает, тело в корне и компонент рядом.

## Решение

Новые модели заводить как **Hybrid**. Отдельного действия это не требует: обычный новый документ (в том числе `documents.add()` из API) уже создаётся Hybrid. Правило формулируется от обратного — **в меню New не выбирать «New Part Design»**, только этот пункт даёт ловушку.

Part Design берётся осознанно и только если проект дорос до BOM, номеров деталей и чертежей на много физических деталей. Для печатных моделей эта дисциплина не окупается.

## Последствия

- Ловушка с аддинами закрыта: в Hybrid Snap Generator и прочие компонент-создающие аддины работают.
- Hybrid ничего не закрывает на будущее. Обратные конвертации по документации API: Hybrid → Assembly можно всегда; Hybrid → Part — пока нет дочерних компонентов; Part → Hybrid — можно (проверено). Не поддерживается Assembly/Hybrid → Part, когда дочерние компоненты уже есть.
- Команды конвертации в UI нет — в меню только `Convert to Parametric/Direct`, sheet metal и меши, к design intent они отношения не имеют. Менять тип существующего документа — через API (`des.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType`) либо обходом через `Add To Assembly` (`NewAssemblyFromPartCommand`).
- Диагностика в одну строку, когда аддин падает непонятно: `des.isModelingInAssemblyEnabled` отвечает `Modeling in assembly API is only applicable to assembly designs` → перед тобой Part или Hybrid; точное значение — `des.designIntent`.
- `DesignIntentTypes` в API помечен как preview feature и может измениться в следующих релизах — на само поведение документов это не влияет, но если проверки перестанут работать, смотреть сюда.
