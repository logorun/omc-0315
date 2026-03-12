import { type ReactNode, useMemo, useState } from "react";

import {
  type ColumnDef,
  type OnChangeFn,
  type SortingState,
  type Updater,
  type VisibilityState,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

import { type AgentRead, type BoardRead } from "@/api/generated/model";
import { DataTable, type DataTableRowAction } from "@/components/tables/DataTable";
import {
  dateCell,
  linkifyCell,
  pillCell,
} from "@/components/tables/cell-formatters";
import { truncateText as truncate } from "@/lib/formatters";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const RETRYABLE_FAILURE_STATUSES = new Set([
  "provision_failed",
  "provision_timeout",
  "update_failed",
  "delete_failed",
]);

type AgentsTableEmptyState = {
  title: string;
  description: string;
  icon?: ReactNode;
  actionHref?: string;
  actionLabel?: string;
};

type AgentsTableProps = {
  agents: AgentRead[];
  boards?: BoardRead[];
  isLoading?: boolean;
  sorting?: SortingState;
  onSortingChange?: OnChangeFn<SortingState>;
  showActions?: boolean;
  hiddenColumns?: string[];
  columnOrder?: string[];
  disableSorting?: boolean;
  stickyHeader?: boolean;
  emptyMessage?: string;
  emptyState?: AgentsTableEmptyState;
  onDelete?: (agent: AgentRead) => void;
  onRetry?: (agent: AgentRead) => void;
};

const DEFAULT_EMPTY_ICON = (
  <svg
    className="h-16 w-16 text-slate-300"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);

function StatusWithTooltip({ status, error }: { status: string | undefined; error?: string | null }) {
  const safeStatus = status ?? "unknown";
  if (!error) {
    return pillCell(safeStatus);
  }
  return (
    <div className="flex items-center gap-1.5">
      {pillCell(safeStatus)}
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-help text-slate-400 hover:text-slate-600">
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p className="max-w-xs">{error}</p>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}

export function AgentsTable({
  agents,
  boards = [],
  isLoading = false,
  sorting,
  onSortingChange,
  showActions = true,
  hiddenColumns,
  columnOrder,
  disableSorting = false,
  stickyHeader = false,
  emptyMessage = "No agents found.",
  emptyState,
  onDelete,
  onRetry,
}: AgentsTableProps) {
  const [internalSorting, setInternalSorting] = useState<SortingState>([
    { id: "name", desc: false },
  ]);
  const resolvedSorting = sorting ?? internalSorting;
  const handleSortingChange: OnChangeFn<SortingState> =
    onSortingChange ??
    ((updater: Updater<SortingState>) => {
      setInternalSorting(updater);
    });

  const sortedAgents = useMemo(() => [...agents], [agents]);
  const columnVisibility = useMemo<VisibilityState>(
    () =>
      Object.fromEntries(
        (hiddenColumns ?? []).map((columnId) => [columnId, false]),
      ),
    [hiddenColumns],
  );
  const boardNameById = useMemo(
    () => new Map(boards.map((board) => [board.id, board.name])),
    [boards],
  );

  const columns = useMemo<ColumnDef<AgentRead>[]>(() => {
    const baseColumns: ColumnDef<AgentRead>[] = [
      {
        accessorKey: "name",
        header: "Agent",
        cell: ({ row }) =>
          linkifyCell({
            href: `/agents/${row.original.id}`,
            label: row.original.name,
            subtitle: `ID ${row.original.id}`,
          }),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => (
          <StatusWithTooltip
            status={row.original.status}
            error={row.original.last_provision_error}
          />
        ),
      },
      {
        accessorKey: "openclaw_session_id",
        header: "Session",
        cell: ({ row }) => (
          <span className="text-sm text-slate-700">
            {truncate(row.original.openclaw_session_id)}
          </span>
        ),
      },
      {
        accessorKey: "board_id",
        header: "Board",
        cell: ({ row }) => {
          const boardId = row.original.board_id;
          if (!boardId) {
            return <span className="text-sm text-slate-700">—</span>;
          }
          const boardName = boardNameById.get(boardId) ?? boardId;
          return linkifyCell({
            href: `/boards/${boardId}`,
            label: boardName,
            block: false,
          });
        },
      },
      {
        accessorKey: "last_seen_at",
        header: "Last seen",
        cell: ({ row }) =>
          dateCell(row.original.last_seen_at, { relative: true }),
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        cell: ({ row }) => dateCell(row.original.updated_at),
      },
    ];

    return baseColumns;
  }, [boardNameById]);

  const rowActions = useMemo((): DataTableRowAction<AgentRead>[] | undefined => {
    if (!showActions) return undefined;

    const actions: DataTableRowAction<AgentRead>[] = [
      {
        key: "edit",
        label: "Edit",
        href: (agent) => `/agents/${agent.id}/edit`,
      },
    ];

    if (onRetry) {
      actions.push({
        key: "retry",
        label: "Retry",
        onClick: onRetry,
        className: (agent) =>
          RETRYABLE_FAILURE_STATUSES.has(agent.status)
            ? "text-amber-600 hover:text-amber-700"
            : "text-slate-300 cursor-not-allowed",
      });
    }

    if (onDelete) {
      actions.push({
        key: "delete",
        label: "Delete",
        onClick: onDelete,
        className: "text-red-600 hover:text-red-700",
      });
    }

    return actions;
  }, [showActions, onRetry, onDelete]);

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: sortedAgents,
    columns,
    enableSorting: !disableSorting,
    state: {
      ...(!disableSorting ? { sorting: resolvedSorting } : {}),
      ...(columnOrder ? { columnOrder } : {}),
      columnVisibility,
    },
    ...(disableSorting ? {} : { onSortingChange: handleSortingChange }),
    getCoreRowModel: getCoreRowModel(),
    ...(disableSorting ? {} : { getSortedRowModel: getSortedRowModel() }),
  });

  return (
    <DataTable
      table={table}
      isLoading={isLoading}
      emptyMessage={emptyMessage}
      stickyHeader={stickyHeader}
      rowActions={
        rowActions
          ? {
              actions: rowActions,
            }
          : undefined
      }
      rowClassName="hover:bg-slate-50"
      cellClassName="px-6 py-4"
      emptyState={
        emptyState
          ? {
              icon: emptyState.icon ?? DEFAULT_EMPTY_ICON,
              title: emptyState.title,
              description: emptyState.description,
              actionHref: emptyState.actionHref,
              actionLabel: emptyState.actionLabel,
            }
          : undefined
      }
    />
  );
}
