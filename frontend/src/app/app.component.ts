import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  ViewChild,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { gsap } from 'gsap';
import * as d3 from 'd3';
import * as THREE from 'three';

type SchemaColumn = {
  name: string;
  type: string;
  constraints: string[];
};

type SchemaTable = {
  name: string;
  columns: SchemaColumn[];
  domain?: string;
  entity_kind?: string;
  graph_modes?: string[];
};

type SchemaRelationship = {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  constraint_name: string;
};

type InsertableColumn = {
  name: string;
  type: string;
  required: boolean;
  foreign_key: boolean;
  primary_key: boolean;
};

type InsertableTable = {
  name: string;
  columns: InsertableColumn[];
};

type SchemaResponse = {
  tables: SchemaTable[];
  views: string[];
  relationships: SchemaRelationship[];
  insertable_tables: InsertableTable[];
  serialized?: string;
};

type InsertResponse = {
  status: string;
  row: Record<string, unknown>;
};

type IndexInfo = {
  name: string;
  definition: string;
};

type TableIntelligence = {
  table_name: string;
  row_count: number;
  primary_keys: string[];
  foreign_keys: string[];
  null_rates: Record<string, number>;
  index_count: number;
  indexes: IndexInfo[];
  sample_rows: Record<string, unknown>[];
  recent_rows: Record<string, unknown>[];
  common_queries: string[];
  domain: string;
  entity_kind: string;
};

type RelationshipPreview = {
  sql: string;
  row_count: number;
  rows: {
    source_row: Record<string, unknown>;
    target_row: Record<string, unknown>;
  }[];
  relationship: SchemaRelationship;
};

type QueryResponse = {
  sql: string;
  results: Record<string, unknown>[];
  explanation: string;
  execution_time: number;
  tables_used: string[];
  complexity_level: string;
  confidence?: number;
  reasoning?: string;
  query_log_id?: number;
};

type PlanNode = {
  'Node Type'?: string;
  'Total Cost'?: number;
  'Plan Rows'?: number;
  'Relation Name'?: string;
  Plans?: PlanNode[];
  [key: string]: unknown;
};

type ExplainResponse = {
  plan: PlanNode | null;
  raw?: unknown;
  summary: string;
};

type RepairResponse = {
  original_sql: string;
  repaired_sql: string;
  results: Record<string, unknown>[];
  fix_summary: string;
  explanation: string;
  tables_used: string[];
  source: string;
};

type MetricsResponse = {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  today_queries: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  fastest_ms: number;
  slowest_ms: number;
  rows_returned: number;
  unique_tables: number;
  success_rate?: number;
};

type ChatTurn = {
  role: 'user' | 'assistant';
  text: string;
  sql?: string;
  rows?: number;
  timestamp: number;
};

type SavedQuery = {
  id: string;
  label: string;
  natural_language: string;
  sql: string;
  saved_at: number;
};

type Achievement = {
  id: string;
  title: string;
  hint: string;
  unlocked_at: number;
};

type ChartType = 'bar' | 'line' | 'pie';

type AppTheme = 'dark' | 'light' | 'oled' | 'sepia';

type HistoryItem = {
  id: number;
  user_input: string;
  generated_sql: string;
  explanation: string;
  execution_status: string;
  execution_time_ms: number;
  result_row_count: number;
  created_at: string;
};

type HistoryResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: HistoryItem[];
};

type AnalyticsRow = {
  department_name: string | null;
  academic_year: string | null;
  term_name: string | null;
  total_grade_points: number | null;
};

type AnalyticsSummary = {
  total_enrollments: number;
  avg_grade_points: number;
  avg_attendance_pct: number;
  total_fees_paid: number;
  departments: number;
  active_terms: number;
};

type DepartmentPerformanceRow = {
  department_name: string;
  enrollment_count: number;
  avg_grade_points: number;
  avg_attendance_pct: number;
  fees_paid: number;
};

type TermTrendRow = {
  academic_year: string;
  term_name: string;
  enrollment_count: number;
  avg_grade_points: number;
  avg_attendance_pct: number;
  fees_paid: number;
};

type FacultyImpactRow = {
  faculty_name: string;
  department_name: string;
  enrollment_count: number;
  avg_grade_points: number;
  avg_attendance_pct: number;
};

type CourseMixRow = {
  course_type: string;
  enrollment_count: number;
  avg_grade_points: number;
  avg_attendance_pct: number;
};

type QueryActivityRow = {
  hour_of_day: number;
  query_count: number;
  avg_latency_ms: number;
};

type AnalyticsResponse = {
  rows: AnalyticsRow[];
  summary: AnalyticsSummary;
  department_performance: DepartmentPerformanceRow[];
  term_trends: TermTrendRow[];
  faculty_impact: FacultyImpactRow[];
  course_mix: CourseMixRow[];
  query_activity: QueryActivityRow[];
};

type Toast = {
  id: number;
  type: 'success' | 'error' | 'info';
  message: string;
};

type ErNode = {
  name: string;
  x: number;
  y: number;
  table: SchemaTable;
  connectedCount: number;
};

type ErNodePosition = {
  x: number;
  y: number;
};

type ErEdge = {
  key: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label: string;
  from_table: string;
  to_table: string;
  from_column: string;
  to_column: string;
};

type GraphMode = 'academic' | 'finance' | 'housing' | 'all';

type CommandAction = {
  id: string;
  label: string;
  hint: string;
  run: () => void;
};

const ADDITIONAL_EXAMPLE_QUERIES = [
  'Show all active students in the Data Science department',
  'List students with CGPA above 9 grouped by department',
  'Find average CGPA by department',
  'Show departments with more than 40 active students',
  'List students admitted after 2023 ordered by admission date',
  'Find students currently on leave',
  'Show undergraduate students with hostel allotments',
  'List students who have no hostel allotment',
  'Find students with attendance below 75 percent',
  'Show top 20 students by final grade points',
  'List faculty members by department and designation',
  'Find professors hired before 2018',
  'Show faculty specialization distribution',
  'List faculty teaching more than two sections',
  'Find the average faculty salary by department',
  'Show faculty teaching hybrid sections',
  'List sections taught by each faculty member this semester',
  'Find faculty with no assigned sections',
  'Show department-wise faculty load',
  'List faculty and the courses they teach',
  'Show all core courses with four credits',
  'List elective courses by department',
  'Find courses at level 300 or above',
  'Show courses with prerequisites',
  'Find courses that have no prerequisites',
  'Show the prerequisite chain for Machine Learning',
  'List courses offered in the Winter semester',
  'Find departments offering the most courses',
  'Show average grade points by course',
  'List courses with low average attendance',
  'Show enrollment count by department',
  'Show enrollment count by course and semester',
  'Find courses with enrollment above section capacity',
  'List students enrolled in Database Systems',
  'Show students enrolled in more than three courses',
  'Find sections with fewer than 10 enrollments',
  'Show completed enrollments with grade A',
  'List dropped enrollments by semester',
  'Find waitlisted students by section',
  'Show enrollment trend across semesters',
  'List all exams scheduled in April 2026',
  'Show exam results with marks above 90',
  'Find average exam marks by course',
  'List students who missed an assignment submission',
  'Show assignment scores by student',
  'Find assignments with average score below 60',
  'Show sections with both exams and assignments',
  'List assessments due this month',
  'Find students with improving grades across semesters',
  'Show grade distribution by department',
  'List unpaid fee invoices',
  'Find overdue invoices by department',
  'Show total fees paid by semester',
  'Find students with partial fee payments',
  'List payment failures by method',
  'Show average scholarship amount by department',
  'Find top fee-paying students',
  'Show hostel fee revenue by semester',
  'List invoices with penalty charges',
  'Show outstanding balance by student',
  'List hostels by occupancy',
  'Find rooms with available capacity',
  'Show students staying in mixed hostels',
  'List active hostel allotments',
  'Find hostel allotments ending this semester',
  'Show hostel occupancy by floor',
  'List students sharing the same room',
  'Find hostels with more than 80 percent occupancy',
  'Show room type distribution',
  'List hostel residents by department',
  'Show department summary with students faculty and courses',
  'Show student transcript for a roll number',
  'List faculty load view for Winter semester',
  'Find departments with average CGPA above 8',
  'Show department-wise course credit totals',
  'Compare student count and faculty count by department',
  'Show departments with the highest fee collection',
  'Find departments with low attendance risk',
  'Show department performance dashboard metrics',
  'List departments ranked by average grade points',
  'Show students and their department names',
  'Find students without any completed enrollment',
  'List faculty and students from the same department',
  'Show courses that share the same faculty',
  'Find students who took both Database Systems and Machine Learning',
  'List students who did not take Cloud Computing',
  'Show faculty who teach courses outside their home department',
  'Find courses with no enrollments',
  'List sections without exams',
  'Show students with both hostel and fee payment records',
  'Show revenue rollup by department and semester',
  'Show cube analysis of average grades by department faculty and semester',
  'Show grouping sets for department and course enrollments',
  'Find monthly payment totals',
  'Show attendance percentiles by department',
  'Rank students within each department by CGPA',
  'Show dense rank of courses by average grade',
  'Assign row numbers to faculty ordered by hire date',
  'Find duplicate-like student names across departments',
  'Show recursive prerequisite paths for all courses'
] as const;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements AfterViewInit, OnDestroy {
  private readonly erStageWidth = 1800;
  private readonly erStageHeight = 1320;
  private readonly erNodeWidth = 220;
  private readonly erNodeHeight = 128;
  private readonly http = inject(HttpClient);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly apiBaseUrl =
    (globalThis as { __env?: { API_BASE_URL?: string } }).__env?.API_BASE_URL ??
    '/api';

  @ViewChild('particleCanvas') particleCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('barChart') barChart?: ElementRef<SVGSVGElement>;
  @ViewChild('areaChart') areaChart?: ElementRef<SVGSVGElement>;
  @ViewChild('donutChart') donutChart?: ElementRef<SVGSVGElement>;
  @ViewChild('heatmapChart') heatmapChart?: ElementRef<SVGSVGElement>;
  @ViewChild('sqlEditor') sqlEditor?: ElementRef<HTMLDivElement>;
  @ViewChild('erCanvas') erCanvas?: ElementRef<HTMLDivElement>;
  @ViewChild('planTree') planTree?: ElementRef<SVGSVGElement>;
  @ViewChild('resultChart') resultChart?: ElementRef<SVGSVGElement>;
  @ViewChild('matrixCanvas') matrixCanvas?: ElementRef<HTMLCanvasElement>;

  readonly exampleQueries = [
    'Show top 10 students by GPA',
    'Count students by department',
    'List students enrolled in Database Systems this semester',
    'Show faculty teaching load this semester',
    'Find prerequisite chain for Machine Learning',
    'Which students have overdue invoices?',
    ...ADDITIONAL_EXAMPLE_QUERIES
  ];

  naturalLanguage = this.exampleQueries[0];
  schema: SchemaResponse = { tables: [], views: [], relationships: [], insertable_tables: [] };
  queryResult: QueryResponse | null = null;
  history: HistoryItem[] = [];
  analyticsRows: AnalyticsRow[] = [];
  analyticsSummary: AnalyticsSummary = {
    total_enrollments: 0,
    avg_grade_points: 0,
    avg_attendance_pct: 0,
    total_fees_paid: 0,
    departments: 0,
    active_terms: 0,
  };
  departmentPerformance: DepartmentPerformanceRow[] = [];
  termTrends: TermTrendRow[] = [];
  facultyImpact: FacultyImpactRow[] = [];
  courseMix: CourseMixRow[] = [];
  queryActivity: QueryActivityRow[] = [];
  analyticsDepartmentMetric: 'enrollment_count' | 'avg_grade_points' | 'avg_attendance_pct' | 'fees_paid' = 'enrollment_count';
  analyticsTrendMetric: 'avg_grade_points' | 'avg_attendance_pct' | 'fees_paid' | 'enrollment_count' = 'avg_grade_points';
  analyticsMixMetric: 'enrollment_count' | 'avg_grade_points' | 'avg_attendance_pct' = 'enrollment_count';
  isLoading = false;
  launched = false;
  transitioning = false;
  sidebarCollapsed = false;
  activeTab: 'query' | 'history' | 'analytics' | 'er' | 'schema' | 'settings' = 'query';
  theme: AppTheme = ((localStorage.getItem('querymind-theme') as AppTheme) || 'dark');
  reduceMotion = localStorage.getItem('querymind-reduced-motion') === 'true';
  errorMessage = '';
  streamTokens: string[] = [];
  toasts: Toast[] = [];
  copied = false;
  universeMode = false;
  overlayStage = 0;
  schemaSearch = '';
  selectedRow: Record<string, unknown> | null = null;
  historyFilter: 'all' | 'success' | 'failed' = 'all';
  insertTableName = '';
  insertPayload = '{}';
  insertResult: Record<string, unknown> | null = null;
  insertError = '';
  insertSubmitting = false;
  selectedErTableName = 'department';
  erZoom = 1;
  erPan = { x: 0, y: 0 };
  erDragging = false;
  erNodeDragging = false;
  erSelecting = false;
  erSelectionBox = { x: 0, y: 0, width: 0, height: 0 };
  erSelectionStart = { x: 0, y: 0 };
  erSelectedGroup: string[] = [];
  erHoveredEdgeKey = '';
  erGraphMode: GraphMode = 'academic';
  erPreviewLoading = false;
  erRelationshipPreview: RelationshipPreview | null = null;
  intelligenceLoading = false;
  intelligenceCache: Record<string, TableIntelligence> = {};
  paletteOpen = false;
  paletteQuery = '';
  showTour = localStorage.getItem('querymind-tour-complete') !== 'true';
  tourStep = 0;

  // Plan / explain state
  planLoading = false;
  planResponse: ExplainResponse | null = null;
  planError = '';

  // Repair state
  repairLoading = false;
  repairResponse: RepairResponse | null = null;
  repairError = '';

  // Multi-turn chat
  conversation: ChatTurn[] = [];
  followupActive = false;

  // Result chart auto-detect
  chartType: ChartType = 'bar';
  chartLabelColumn = '';
  chartValueColumn = '';
  showResultChart = false;

  // Voice
  voiceListening = false;
  voiceSupported = typeof window !== 'undefined' && (
    'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
  );
  speechSynthSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  private recognition: { stop: () => void; start: () => void } | null = null;

  // Metrics strip
  metrics: MetricsResponse = {
    total_queries: 0,
    successful_queries: 0,
    failed_queries: 0,
    today_queries: 0,
    avg_latency_ms: 0,
    p95_latency_ms: 0,
    fastest_ms: 0,
    slowest_ms: 0,
    rows_returned: 0,
    unique_tables: 0,
  };

  // Saved queries / share
  savedQueries: SavedQuery[] = [];
  shareLink = '';

  // Achievements
  achievements: Achievement[] = [];

  // Matrix mode
  matrixModeActive = false;
  private matrixFrame = 0;

  // Stream state
  streamingSql = '';
  private currentStreamSource: EventSource | null = null;
  private erDragStart = { x: 0, y: 0 };
  private erNodeDragName = '';
  private erNodeDragOffset = { x: 0, y: 0 };
  private erLastPointer = { x: 0, y: 0, at: 0 };
  private erVelocity = { x: 0, y: 0 };
  private erNodePositions: Record<string, ErNodePosition> = {};

  private renderer?: THREE.WebGLRenderer;
  private scene?: THREE.Scene;
  private camera?: THREE.PerspectiveCamera;
  private particleFrame = 0;
  private particles?: THREE.Points;
  private lines?: THREE.LineSegments;
  private mouse = { x: 0, y: 0 };
  private konamiBuffer: string[] = [];
  private editor: import('monaco-editor/esm/vs/editor/editor.api.js').editor.IStandaloneCodeEditor | null = null;
  private toastId = 0;
  private readonly erFocusTableNames = [
    'department',
    'person',
    'student',
    'faculty',
    'course',
    'course_prerequisite',
    'semester',
    'section',
    'enrollment',
    'assessment',
    'fee_invoice',
    'hostel_allotment'
  ];

  private get commandActions(): CommandAction[] {
    return [
      {
        id: 'focus-student',
        label: 'Focus student entity',
        hint: 'ER diagram',
        run: () => {
          this.setTab('er');
          this.selectErTable('student');
        },
      },
      {
        id: 'insert-fee-invoice',
        label: 'Insert into fee_invoice',
        hint: 'Schema console',
        run: () => {
          this.setTab('schema');
          this.focusInsertTable('fee_invoice');
        },
      },
      {
        id: 'run-transcript',
        label: 'Run transcript query',
        hint: 'Query workspace',
        run: () => {
          this.setTab('query');
          this.useExample('Show student transcript for a roll number');
        },
      },
      {
        id: 'open-analytics',
        label: 'Open analytics dashboard',
        hint: 'OLAP view',
        run: () => this.setTab('analytics'),
      },
      ...this.schema.tables.slice(0, 8).map((table) => ({
        id: `focus-${table.name}`,
        label: `Focus ${table.name}`,
        hint: `${table.domain ?? 'schema'} entity`,
        run: () => {
          this.setTab('er');
          this.selectErTable(table.name);
        },
      })),
    ];
  }

  constructor() {
    document.documentElement.dataset['theme'] = this.theme;
    document.documentElement.dataset['motion'] = this.reduceMotion ? 'reduced' : 'full';
    this.loadSchema();
    this.loadHistory();
    this.loadAnalytics();
    this.loadMetrics();
    this.loadSavedQueries();
    this.loadAchievements();
    this.hydrateFromShareLink();
  }

  ngAfterViewInit(): void {
    this.initParticles();
    this.animateHero();
    this.renderCharts();
    void this.initMonaco();
  }

  ngOnDestroy(): void {
    cancelAnimationFrame(this.particleFrame);
    this.renderer?.dispose();
    this.editor?.dispose();
  }

  get filteredSchema(): SchemaTable[] {
    const query = this.schemaSearch.trim().toLowerCase();
    if (!query) {
      return this.schema.tables;
    }
    return this.schema.tables
      .map((table) => ({
        ...table,
        columns: table.columns.filter((column) =>
          `${table.name}.${column.name}.${column.type}`.toLowerCase().includes(query)
        )
      }))
      .filter((table) => table.name.toLowerCase().includes(query) || table.columns.length > 0);
  }

  get filteredHistory(): HistoryItem[] {
    if (this.historyFilter === 'all') {
      return this.history;
    }
    return this.history.filter((item) => item.execution_status.toLowerCase() === this.historyFilter);
  }

  get displayedColumns(): string[] {
    return this.queryResult?.results.length ? Object.keys(this.queryResult.results[0]) : [];
  }

  get activeTableIntelligence(): TableIntelligence | null {
    return this.selectedErTableName ? this.intelligenceCache[this.selectedErTableName] ?? null : null;
  }

  get selectedInsertTable(): InsertableTable | undefined {
    return this.schema.insertable_tables.find((table) => table.name === this.insertTableName);
  }

  get topFacultyImpact(): FacultyImpactRow[] {
    return this.facultyImpact.slice(0, 5);
  }

  get selectedErTable(): SchemaTable | undefined {
    return this.schema.tables.find((table) => table.name === this.selectedErTableName);
  }

  get selectedErRelationships(): SchemaRelationship[] {
    if (!this.selectedErTableName) {
      return [];
    }
    return this.schema.relationships.filter(
      (relationship) =>
        relationship.from_table === this.selectedErTableName || relationship.to_table === this.selectedErTableName
    );
  }

  get erNodes(): ErNode[] {
    const focusTables = this.schema.tables
      .filter((table) => this.tableMatchesGraphMode(table))
      .filter((table) => this.erGraphMode === 'all' || this.erFocusTableNames.includes(table.name) || table.graph_modes?.includes(this.erGraphMode));
    return focusTables.map((table, index) => ({
      name: table.name,
      x: this.erNodePositions[table.name]?.x ?? 36 + (index % 5) * 340,
      y: this.erNodePositions[table.name]?.y ?? 36 + Math.floor(index / 5) * 235,
      table,
      connectedCount: this.schema.relationships.filter(
        (relationship) => relationship.from_table === table.name || relationship.to_table === table.name
      ).length
    }));
  }

  get erEdges(): ErEdge[] {
    const nodeLookup = new Map(this.erNodes.map((node) => [node.name, node]));
    return this.schema.relationships
      .filter((relationship) => nodeLookup.has(relationship.from_table) && nodeLookup.has(relationship.to_table))
      .map((relationship) => {
        const fromNode = nodeLookup.get(relationship.from_table) as ErNode;
        const toNode = nodeLookup.get(relationship.to_table) as ErNode;
        return {
          key: relationship.constraint_name,
          x1: fromNode.x + 110,
          y1: fromNode.y + 78,
          x2: toNode.x + 110,
          y2: toNode.y + 78,
          label: `${relationship.from_table}.${relationship.from_column} → ${relationship.to_table}.${relationship.to_column}`,
          from_table: relationship.from_table,
          to_table: relationship.to_table,
          from_column: relationship.from_column,
          to_column: relationship.to_column,
        };
      });
  }

  get filteredCommandActions(): CommandAction[] {
    const query = this.paletteQuery.trim().toLowerCase();
    return this.commandActions.filter((action) => `${action.label} ${action.hint}`.toLowerCase().includes(query));
  }

  get erViewportBox(): { width: number; height: number; x: number; y: number } {
    const canvas = this.erCanvas?.nativeElement;
    const canvasWidth = canvas?.clientWidth ?? 640;
    const canvasHeight = canvas?.clientHeight ?? 480;
    const stageWidth = this.erStageWidth * this.erZoom;
    const stageHeight = this.erStageHeight * this.erZoom;
    return {
      width: Math.max(36, (canvasWidth / stageWidth) * 160),
      height: Math.max(28, (canvasHeight / stageHeight) * 130),
      x: Math.max(0, (-this.erPan.x / stageWidth) * 160),
      y: Math.max(0, (-this.erPan.y / stageHeight) * 130),
    };
  }

  launchApp(): void {
    if (this.launched || this.transitioning) {
      return;
    }
    this.transitioning = true;
    this.cdr.detectChanges();
    const revealApp = () => {
      this.launched = true;
      this.cdr.detectChanges();
      setTimeout(() => {
        this.renderCharts();
        void this.initMonaco();
        gsap.fromTo('.app-shell', { y: 28, opacity: 0 }, { y: 0, opacity: 1, duration: 0.42, ease: 'power3.out' });
      });
    };
    const timeline = gsap.timeline({
      onComplete: () => {
        this.transitioning = false;
        setTimeout(() => {
          this.renderCharts();
          void this.initMonaco();
        });
      }
    });
    timeline
      .to('.hero-content', { y: -52, opacity: 0, duration: 0.45, ease: 'power3.inOut' })
      .to('.particle-canvas', { scale: 1.8, opacity: 0, duration: 0.55, ease: 'power3.inOut' }, '<')
      .fromTo('.launch-wipe', { yPercent: 100 }, { yPercent: 0, duration: 0.55, ease: 'power4.inOut', immediateRender: true }, '<')
      .call(revealApp)
      .to('.launch-wipe', { yPercent: -100, duration: 0.35, ease: 'power2.inOut' });
    setTimeout(() => {
      if (!this.launched) {
        revealApp();
      }
      this.transitioning = false;
      this.cdr.detectChanges();
      gsap.set('.launch-wipe', { yPercent: -100 });
    }, 1200);
  }

  returnToLanding(): void {
    this.launched = false;
    this.transitioning = false;
    this.activeTab = 'query';
    this.cdr.detectChanges();
    setTimeout(() => {
      gsap.set('.hero-content', { y: 0, opacity: 1 });
      gsap.set('.particle-canvas', { scale: 1, opacity: 1 });
      gsap.set('.launch-wipe', { yPercent: 100 });
      this.animateHero();
    });
  }

  setTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;
    gsap.fromTo('.route-panel', { x: 26, opacity: 0 }, { x: 0, opacity: 1, duration: 0.3, ease: 'power2.out' });
    setTimeout(() => {
      this.renderCharts();
      void this.initMonaco();
    });
  }

  loadSchema(): void {
    this.http.get<SchemaResponse>(`${this.apiBaseUrl}/schema`).subscribe({
      next: (response) => {
        this.schema = response;
        if (!response.tables.some((table) => table.name === this.selectedErTableName) && response.tables.length) {
          this.selectedErTableName = response.tables[0].name;
        }
        if (this.selectedErTableName) {
          this.loadTableIntelligence(this.selectedErTableName);
        }
        if (!this.insertTableName && response.insertable_tables.length) {
          this.insertTableName = response.insertable_tables[0].name;
          this.populateInsertTemplate();
        }
      },
      error: () => {
        this.errorMessage = 'Failed to load schema metadata.';
      }
    });
  }

  loadHistory(): void {
    this.http.get<HistoryResponse>(`${this.apiBaseUrl}/history`).subscribe({
      next: (response) => {
        this.history = response.results;
      }
    });
  }

  loadAnalytics(): void {
    this.http.get<AnalyticsResponse>(`${this.apiBaseUrl}/analytics/rollup`).subscribe({
      next: (response) => {
        this.analyticsRows = response.rows.filter((row) => row.department_name !== null);
        this.analyticsSummary = response.summary;
        this.departmentPerformance = response.department_performance;
        this.termTrends = response.term_trends;
        this.facultyImpact = response.faculty_impact;
        this.courseMix = response.course_mix;
        this.queryActivity = response.query_activity;
        setTimeout(() => this.renderCharts());
      }
    });
  }

  submitQuery(): void {
    if (this.naturalLanguage.trim().toUpperCase() === 'SELECT * FROM UNIVERSE') {
      this.triggerUniverse();
      return;
    }

    const promptText = this.naturalLanguage;
    const priorSql = this.followupActive && this.queryResult?.sql ? this.queryResult.sql : null;

    this.isLoading = true;
    this.errorMessage = '';
    this.streamTokens = [];
    this.streamingSql = '';
    this.planResponse = null;
    this.repairResponse = null;
    this.overlayStage = 1;
    this.selectedRow = null;
    this.startSse();

    gsap.timeline()
      .fromTo('.thinking-overlay', { y: -32, opacity: 0 }, { y: 0, opacity: 1, duration: 0.25 })
      .to({}, { duration: 0.35, onComplete: () => { this.overlayStage = 2; } })
      .to({}, { duration: 0.35, onComplete: () => { this.overlayStage = 3; } });

    const payload: { natural_language: string; prior_sql?: string } = {
      natural_language: promptText,
    };
    if (priorSql) {
      payload.prior_sql = priorSql;
    }

    this.http
      .post<QueryResponse>(`${this.apiBaseUrl}/query`, payload)
      .subscribe({
        next: (response) => {
          this.queryResult = response;
          this.isLoading = false;
          this.overlayStage = 4;
          this.streamingSql = response.sql;
          this.conversation = [
            ...this.conversation,
            { role: 'user', text: promptText, timestamp: Date.now() },
            {
              role: 'assistant',
              text: response.explanation,
              sql: response.sql,
              rows: response.results.length,
              timestamp: Date.now(),
            },
          ];
          this.loadHistory();
          this.loadMetrics();
          this.showToast('success', `Returned ${response.results.length} rows`);
          this.handleQueryAchievements(response);
          this.refreshChartConfig();
          this.updateShareLink();
          setTimeout(() => {
            void this.initMonaco().then(() => this.updateEditor(response.sql));
            this.renderResultChart();
          });
          setTimeout(() => gsap.to('.thinking-overlay', { y: -32, opacity: 0, duration: 0.22 }), 250);
          setTimeout(() => gsap.fromTo('.result-row', { y: 12, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.03 }), 0);
        },
        error: (error: { error?: { detail?: string } }) => {
          this.errorMessage = error.error?.detail ?? 'Query execution failed.';
          this.isLoading = false;
          this.overlayStage = 0;
          this.showToast('error', this.errorMessage);
        }
      });
  }

  toggleFollowup(): void {
    this.followupActive = !this.followupActive;
    if (this.followupActive) {
      this.showToast('info', 'Follow-up mode: your next prompt will refine the current SQL.');
    }
  }

  resetConversation(): void {
    this.conversation = [];
    this.followupActive = false;
    this.showToast('info', 'Chat thread cleared.');
  }

  runEtl(): void {
    this.http.post(`${this.apiBaseUrl}/admin/etl/run`, {}).subscribe({
      next: () => {
        this.showToast('success', 'ETL completed');
        this.loadAnalytics();
      },
      error: () => this.showToast('error', 'ETL failed')
    });
  }

  useExample(query: string): void {
    this.naturalLanguage = '';
    const chars = query.split('');
    chars.forEach((char, index) => {
      setTimeout(() => {
        this.naturalLanguage += char;
      }, index * 14);
    });
  }

  fillTableQuery(tableName: string): void {
    this.animateEntityRoute(tableName);
    this.useExample(`Show me all records from ${tableName}`);
    this.setTab('query');
  }

  getSchemaPreviewColumns(tableName: string): SchemaColumn[] {
    return this.schema.tables.find((table) => table.name === tableName)?.columns.slice(0, 5) ?? [];
  }

  isErNodeSelected(tableName: string): boolean {
    return this.selectedErTableName === tableName;
  }

  isErNodeConnected(tableName: string): boolean {
    return this.selectedErRelationships.some(
      (relationship) => relationship.from_table === tableName || relationship.to_table === tableName
    );
  }

  isErEdgeHighlighted(edge: ErEdge): boolean {
    return edge.from_table === this.selectedErTableName || edge.to_table === this.selectedErTableName;
  }

  selectErTable(tableName: string): void {
    this.selectedErTableName = tableName;
    this.loadTableIntelligence(tableName);
    this.centerErTable(tableName);
    gsap.fromTo('.er-inspector', { y: 10, opacity: 0.6 }, { y: 0, opacity: 1, duration: 0.2, ease: 'power2.out' });
  }

  focusInsertTable(tableName: string): void {
    this.animateEntityRoute(tableName);
    this.insertTableName = tableName;
    this.onInsertTableChange();
    this.setTab('schema');
  }

  zoomErDiagram(delta: number): void {
    this.erZoom = Math.max(0.75, Math.min(1.6, Number((this.erZoom + delta).toFixed(2))));
  }

  resetErDiagram(): void {
    this.erZoom = 1;
    this.erPan = { x: 0, y: 0 };
    this.erNodePositions = {};
  }

  startErPan(event: MouseEvent): void {
    if ((event.target as HTMLElement).closest('.er-node, .er-zoom-controls, .er-actions, .chip')) {
      return;
    }
    if (event.shiftKey) {
      const rect = this.erCanvas?.nativeElement.getBoundingClientRect();
      if (!rect) {
        return;
      }
      this.erSelectionStart = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      this.erSelecting = true;
      this.erSelectionBox = {
        x: this.erSelectionStart.x,
        y: this.erSelectionStart.y,
        width: 0,
        height: 0,
      };
      return;
    }
    this.erDragging = true;
    this.erDragStart = {
      x: event.clientX - this.erPan.x,
      y: event.clientY - this.erPan.y
    };
    this.erLastPointer = { x: event.clientX, y: event.clientY, at: performance.now() };
  }

  startErNodeDrag(event: MouseEvent, node: ErNode): void {
    event.preventDefault();
    event.stopPropagation();
    const canvas = this.erCanvas?.nativeElement;
    if (!canvas) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const pointerX = (event.clientX - rect.left - this.erPan.x) / this.erZoom;
    const pointerY = (event.clientY - rect.top - this.erPan.y) / this.erZoom;
    this.erNodeDragging = true;
    this.erNodeDragName = node.name;
    this.erNodeDragOffset = {
      x: pointerX - node.x,
      y: pointerY - node.y,
    };
  }

  onErWheel(event: WheelEvent): void {
    event.preventDefault();
    this.zoomErDiagram(event.deltaY > 0 ? -0.08 : 0.08);
  }

  setErGraphMode(mode: GraphMode): void {
    this.erGraphMode = mode;
    this.erSelectedGroup = [];
    this.resetErDiagram();
  }

  loadTableIntelligence(tableName: string): void {
    if (this.intelligenceCache[tableName]) {
      return;
    }
    this.intelligenceLoading = true;
    this.http.get<TableIntelligence>(`${this.apiBaseUrl}/schema/intelligence?table_name=${encodeURIComponent(tableName)}`).subscribe({
      next: (response) => {
        this.intelligenceCache = { ...this.intelligenceCache, [tableName]: response };
        this.intelligenceLoading = false;
      },
      error: () => {
        this.intelligenceLoading = false;
      }
    });
  }

  previewRelationship(relationship: SchemaRelationship): void {
    this.erPreviewLoading = true;
    const query = new URLSearchParams({
      from_table: relationship.from_table,
      from_column: relationship.from_column,
      to_table: relationship.to_table,
      to_column: relationship.to_column,
    });
    this.http.get<RelationshipPreview>(`${this.apiBaseUrl}/schema/relationship-preview?${query.toString()}`).subscribe({
      next: (response) => {
        this.erRelationshipPreview = response;
        this.erPreviewLoading = false;
      },
      error: () => {
        this.erPreviewLoading = false;
        this.showToast('error', 'Relationship preview failed');
      }
    });
  }

  hoverRelationship(key: string): void {
    this.erHoveredEdgeKey = key;
  }

  clearRelationshipHover(): void {
    this.erHoveredEdgeKey = '';
  }

  openPalette(): void {
    this.paletteOpen = true;
    this.paletteQuery = '';
    setTimeout(() => document.getElementById('command-palette-input')?.focus(), 0);
  }

  closePalette(): void {
    this.paletteOpen = false;
  }

  runCommand(action: CommandAction): void {
    this.closePalette();
    action.run();
  }

  nextTourStep(): void {
    if (this.tourStep >= 3) {
      this.dismissTour();
      return;
    }
    this.tourStep += 1;
    if (this.tourStep === 1) {
      this.setTab('er');
    }
    if (this.tourStep === 2) {
      this.selectErTable('student');
    }
    if (this.tourStep === 3) {
      this.setTab('schema');
      this.focusInsertTable('department');
    }
  }

  dismissTour(): void {
    this.showTour = false;
    localStorage.setItem('querymind-tour-complete', 'true');
  }

  useCommonQuery(query: string): void {
    this.setTab('query');
    this.useExample(query);
  }

  getNullRate(columnName: string): number {
    return this.activeTableIntelligence?.null_rates[columnName] ?? 0;
  }

  tableMatchesGraphMode(table: SchemaTable): boolean {
    return this.erGraphMode === 'all' || table.graph_modes?.includes(this.erGraphMode) === true;
  }

  isErNodeQueryLinked(tableName: string): boolean {
    return this.queryResult?.tables_used.includes(tableName) ?? false;
  }

  isErEdgeQueryLinked(edge: ErEdge): boolean {
    const tables = this.queryResult?.tables_used ?? [];
    return tables.includes(edge.from_table) && tables.includes(edge.to_table);
  }

  isErEdgeLabelVisible(edge: ErEdge): boolean {
    return true;
  }

  isErNodeGroupSelected(tableName: string): boolean {
    return this.erSelectedGroup.includes(tableName);
  }

  onInsertTableChange(): void {
    this.insertResult = null;
    this.insertError = '';
    this.populateInsertTemplate();
  }

  populateInsertTemplate(): void {
    const table = this.selectedInsertTable;
    if (!table) {
      this.insertPayload = '{}';
      return;
    }
    const exampleRecord = Object.fromEntries(
      table.columns
        .filter((column) => !column.primary_key || column.required)
        .slice(0, 6)
        .map((column) => [column.name, this.exampleValueForColumn(column)])
    );
    this.insertPayload = JSON.stringify(exampleRecord, null, 2);
  }

  submitInsertRecord(): void {
    if (!this.insertTableName) {
      this.insertError = 'Choose a table before inserting.';
      return;
    }

    let parsedRecord: Record<string, unknown>;
    try {
      parsedRecord = JSON.parse(this.insertPayload) as Record<string, unknown>;
    } catch {
      this.insertError = 'Insert payload must be valid JSON.';
      return;
    }

    this.insertSubmitting = true;
    this.insertError = '';
    this.insertResult = null;

    this.http
      .post<InsertResponse>(`${this.apiBaseUrl}/records/insert`, {
        table_name: this.insertTableName,
        record: parsedRecord
      })
      .subscribe({
        next: (response) => {
          this.insertSubmitting = false;
          this.insertResult = response.row;
          this.showToast('success', `Inserted row into ${this.insertTableName}`);
          this.loadSchema();
        },
        error: (error: { error?: { detail?: string } }) => {
          this.insertSubmitting = false;
          this.insertError = error.error?.detail ?? 'Insert failed.';
          this.showToast('error', this.insertError);
        }
      });
  }

  copySql(): void {
    if (!this.queryResult?.sql) {
      return;
    }
    void navigator.clipboard.writeText(this.queryResult.sql);
    this.copied = true;
    this.showToast('success', 'SQL copied');
    setTimeout(() => (this.copied = false), 1600);
  }

  selectRow(row: Record<string, unknown>): void {
    this.selectedRow = row;
  }

  copyRow(): void {
    if (!this.selectedRow) {
      return;
    }
    void navigator.clipboard.writeText(JSON.stringify(this.selectedRow, null, 2));
    this.showToast('success', 'Row copied as JSON');
  }

  queryRelated(): void {
    const row = this.selectedRow;
    if (!row) {
      return;
    }
    const key = Object.keys(row).find((item) => item.endsWith('_id')) ?? Object.keys(row)[0];
    this.useExample(`Show me related records for ${key} ${String(row[key])}`);
  }

  toggleTheme(): void {
    const order: AppTheme[] = ['dark', 'light', 'oled', 'sepia'];
    const next = order[(order.indexOf(this.theme) + 1) % order.length];
    this.theme = next;
    document.documentElement.dataset['theme'] = this.theme;
    localStorage.setItem('querymind-theme', this.theme);
    this.showToast('info', `Theme: ${this.theme}`);
  }

  themeIcon(theme: AppTheme): string {
    switch (theme) {
      case 'dark':
        return '☾';
      case 'light':
        return '☀';
      case 'oled':
        return '◉';
      case 'sepia':
        return '✶';
    }
  }

  analyticsMetricLabel(metric: 'enrollment_count' | 'avg_grade_points' | 'avg_attendance_pct' | 'fees_paid'): string {
    switch (metric) {
      case 'enrollment_count':
        return 'Enrollments';
      case 'avg_grade_points':
        return 'Average grade';
      case 'avg_attendance_pct':
        return 'Attendance %';
      case 'fees_paid':
        return 'Fees paid';
    }
  }

  formatAnalyticsValue(value: number, metric: 'enrollment_count' | 'avg_grade_points' | 'avg_attendance_pct' | 'fees_paid'): string {
    if (metric === 'fees_paid') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(value);
    }
    if (metric === 'avg_attendance_pct') {
      return `${value.toFixed(1)}%`;
    }
    if (metric === 'avg_grade_points') {
      return value.toFixed(2);
    }
    return Math.round(value).toString();
  }

  toggleReducedMotion(): void {
    this.reduceMotion = !this.reduceMotion;
    document.documentElement.dataset['motion'] = this.reduceMotion ? 'reduced' : 'full';
    localStorage.setItem('querymind-reduced-motion', String(this.reduceMotion));
    this.showToast('info', `Motion ${this.reduceMotion ? 'reduced' : 'full'}`);
  }

  @HostListener('document:keydown', ['$event'])
  handleKeydown(event: KeyboardEvent): void {
    const key = event.key.toLowerCase();
    if ((event.metaKey || event.ctrlKey) && key === 'enter') {
      event.preventDefault();
      this.submitQuery();
    }
    if ((event.metaKey || event.ctrlKey) && key === 'k') {
      event.preventDefault();
      this.openPalette();
      return;
    }
    if (key === 'escape') {
      if (this.paletteOpen) {
        this.closePalette();
      } else {
        this.queryResult = null;
        this.selectedRow = null;
        this.erRelationshipPreview = null;
      }
    }
    if (key === 'enter' && this.paletteOpen && this.filteredCommandActions[0]) {
      event.preventDefault();
      this.runCommand(this.filteredCommandActions[0]);
    }
    this.trackKonami(event.key);
  }

  @HostListener('window:resize')
  handleResize(): void {
    this.resizeParticles();
    this.renderCharts();
  }

  @HostListener('document:mousemove', ['$event'])
  handleMouseMove(event: MouseEvent): void {
    this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    document.documentElement.style.setProperty('--cursor-x', `${event.clientX}px`);
    document.documentElement.style.setProperty('--cursor-y', `${event.clientY}px`);
    if (this.erNodeDragging) {
      const canvas = this.erCanvas?.nativeElement;
      if (!canvas || !this.erNodeDragName) {
        return;
      }
      const rect = canvas.getBoundingClientRect();
      const x = (event.clientX - rect.left - this.erPan.x) / this.erZoom - this.erNodeDragOffset.x;
      const y = (event.clientY - rect.top - this.erPan.y) / this.erZoom - this.erNodeDragOffset.y;
      this.erNodePositions = {
        ...this.erNodePositions,
        [this.erNodeDragName]: {
          x: Math.max(8, Math.min(this.erStageWidth - this.erNodeWidth - 8, x)),
          y: Math.max(8, Math.min(this.erStageHeight - this.erNodeHeight - 8, y)),
        },
      };
      return;
    }
    if (this.erDragging) {
      const now = performance.now();
      const deltaTime = Math.max(16, now - this.erLastPointer.at);
      this.erVelocity = {
        x: (event.clientX - this.erLastPointer.x) / deltaTime * 18,
        y: (event.clientY - this.erLastPointer.y) / deltaTime * 18,
      };
      this.erPan = {
        x: event.clientX - this.erDragStart.x,
        y: event.clientY - this.erDragStart.y
      };
      this.erLastPointer = { x: event.clientX, y: event.clientY, at: now };
    }
    if (this.erSelecting) {
      const rect = this.erCanvas?.nativeElement.getBoundingClientRect();
      if (!rect) {
        return;
      }
      this.erSelectionBox = {
        x: Math.min(this.erSelectionStart.x, event.clientX - rect.left),
        y: Math.min(this.erSelectionStart.y, event.clientY - rect.top),
        width: Math.abs(event.clientX - rect.left - this.erSelectionStart.x),
        height: Math.abs(event.clientY - rect.top - this.erSelectionStart.y),
      };
    }
  }

  @HostListener('document:mouseup')
  handleMouseUp(): void {
    if (this.erNodeDragging) {
      this.erNodeDragging = false;
      this.erNodeDragName = '';
      return;
    }
    if (this.erDragging) {
      gsap.to(this.erPan, {
        x: this.erPan.x + this.erVelocity.x * 18,
        y: this.erPan.y + this.erVelocity.y * 18,
        duration: 0.45,
        ease: 'power3.out',
      });
    }
    if (this.erSelecting) {
      this.finishErSelection();
    }
    this.erDragging = false;
    this.erSelecting = false;
  }

  private animateHero(): void {
    gsap.fromTo('.hero-word', { y: 38, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.11, duration: 0.72, ease: 'power3.out' });
    gsap.fromTo('.hero-subtitle, .hero-actions, .feature-strip', { y: 20, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.08, delay: 0.35 });
  }

  private exampleValueForColumn(column: InsertableColumn): string | number | boolean {
    const name = column.name.toLowerCase();
    const type = column.type.toLowerCase();
    const enumDefaults: Record<string, string> = {
      person_type: 'student',
      program_level: 'undergraduate',
      term_name: 'Monsoon',
      course_type: 'core',
      hostel_type: 'mixed',
      room_type: 'double',
      delivery_mode: 'offline',
      enrollment_status: 'enrolled',
      assessment_type: 'assignment',
      exam_mode: 'offline',
      submission_mode: 'portal',
      payment_method: 'upi',
      payment_status: 'success',
    };
    if (name in enumDefaults) {
      return enumDefaults[name];
    }
    if (name.includes('email')) {
      return 'new.record@querymind.local';
    }
    if (name.includes('phone')) {
      return '+91-9000000000';
    }
    if (name.includes('code')) {
      return `NEW_${column.name.toUpperCase()}`;
    }
    if (name.includes('date')) {
      return '2026-04-08';
    }
    if (name.includes('status')) {
      return 'active';
    }
    if (name.includes('academic_year')) {
      return '2026-27';
    }
    if (name.includes('gender')) {
      return 'female';
    }
    if (name.includes('grade_letter')) {
      return 'A';
    }
    if (type.includes('int') || type.includes('numeric') || type.includes('double')) {
      return 1;
    }
    if (type.includes('bool')) {
      return true;
    }
    return `Sample ${column.name.replace(/_/g, ' ')}`;
  }

  private centerErTable(tableName: string): void {
    const canvas = this.erCanvas?.nativeElement;
    const node = this.erNodes.find((item) => item.name === tableName);
    if (!canvas || !node) {
      return;
    }
    const targetPan = {
      x: canvas.clientWidth / 2 - (node.x + 110) * this.erZoom,
      y: Math.max(18, canvas.clientHeight / 2 - (node.y + 78) * this.erZoom),
    };
    gsap.to(this.erPan, { ...targetPan, duration: 0.35, ease: 'power2.out' });
  }

  private animateEntityRoute(tableName: string): void {
    if (this.activeTab !== 'er') {
      return;
    }
    this.selectedErTableName = tableName;
    gsap.fromTo('.er-node.selected', { scale: 1 }, { scale: 1.06, duration: 0.12, yoyo: true, repeat: 1 });
  }

  private finishErSelection(): void {
    const canvas = this.erCanvas?.nativeElement;
    if (!canvas) {
      return;
    }
    const selection = this.erSelectionBox;
    const selected = this.erNodes
      .filter((node) => {
        const x = node.x * this.erZoom + this.erPan.x;
        const y = node.y * this.erZoom + this.erPan.y;
        const width = this.erNodeWidth * this.erZoom;
        const height = this.erNodeHeight * this.erZoom;
        return (
          x < selection.x + selection.width &&
          x + width > selection.x &&
          y < selection.y + selection.height &&
          y + height > selection.y
        );
      })
      .map((node) => node.name);
    this.erSelectedGroup = selected;
    this.erSelectionBox = { x: 0, y: 0, width: 0, height: 0 };
  }

  private initParticles(): void {
    const canvas = this.particleCanvas?.nativeElement;
    if (!canvas) {
      return;
    }
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 1000);
    this.camera.position.z = 84;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.resizeParticles();

    const count = 2000;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      positions[i * 3] = (Math.random() - 0.5) * 160;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 90;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 120;
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0x8b5cf6,
      size: 0.38,
      transparent: true,
      opacity: 0.72,
      blending: THREE.AdditiveBlending
    });
    this.particles = new THREE.Points(particleGeometry, particleMaterial);
    this.scene.add(this.particles);

    const linePositions = new Float32Array(420 * 6);
    for (let i = 0; i < 420; i += 1) {
      const a = Math.floor(Math.random() * count);
      const b = Math.floor(Math.random() * count);
      linePositions.set(positions.slice(a * 3, a * 3 + 3), i * 6);
      linePositions.set(positions.slice(b * 3, b * 3 + 3), i * 6 + 3);
    }
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    this.lines = new THREE.LineSegments(
      lineGeometry,
      new THREE.LineBasicMaterial({ color: 0x6366f1, transparent: true, opacity: 0.12 })
    );
    this.scene.add(this.lines);
    this.renderParticles();
  }

  private renderParticles(): void {
    if (document.hidden || !this.renderer || !this.scene || !this.camera) {
      this.particleFrame = requestAnimationFrame(() => this.renderParticles());
      return;
    }
    if (this.particles) {
      this.particles.rotation.y += 0.0018 + this.mouse.x * 0.0008;
      this.particles.rotation.x += 0.0008 + this.mouse.y * 0.0006;
    }
    if (this.lines) {
      this.lines.rotation.copy(this.particles?.rotation ?? new THREE.Euler());
    }
    this.renderer.render(this.scene, this.camera);
    this.particleFrame = requestAnimationFrame(() => this.renderParticles());
  }

  private resizeParticles(): void {
    if (!this.renderer || !this.camera) {
      return;
    }
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  private async initMonaco(): Promise<void> {
    if (!this.sqlEditor?.nativeElement || this.editor) {
      return;
    }
    const monaco = await import('monaco-editor/esm/vs/editor/editor.api.js');
    monaco.editor.defineTheme('querymind', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword.sql', foreground: '4ade80' },
        { token: 'string.sql', foreground: 'a78bfa' }
      ],
      colors: {
        'editor.background': '#08080d',
        'editorLineNumber.foreground': '#475569'
      }
    });
    this.editor = monaco.editor.create(this.sqlEditor.nativeElement, {
      value: this.queryResult?.sql ?? '-- Submit a query to inspect generated SQL',
      language: 'sql',
      theme: 'querymind',
      readOnly: false,
      minimap: { enabled: false },
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 13,
      lineNumbers: 'on',
      automaticLayout: true,
      scrollBeyondLastLine: false,
      suggestOnTriggerCharacters: true,
      quickSuggestions: { other: true, strings: true, comments: true },
    });
    this.registerSqlAutocomplete(monaco);
  }

  private autocompleteRegistered = false;
  private registerSqlAutocomplete(monaco: typeof import('monaco-editor/esm/vs/editor/editor.api.js')): void {
    if (this.autocompleteRegistered) {
      return;
    }
    this.autocompleteRegistered = true;
    monaco.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };
        const tableSuggestions = this.schema.tables.map((table) => ({
          label: table.name,
          kind: monaco.languages.CompletionItemKind.Class,
          insertText: table.name,
          detail: `${table.entity_kind ?? 'entity'} · ${table.columns.length} columns`,
          documentation: table.columns
            .slice(0, 6)
            .map((column) => `${column.name}: ${column.type}`)
            .join('\n'),
          range,
        }));
        const columnSuggestions = this.schema.tables.flatMap((table) =>
          table.columns.map((column) => ({
            label: `${table.name}.${column.name}`,
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: column.name,
            detail: `${table.name} · ${column.type}`,
            range,
          }))
        );
        const keywordSuggestions = [
          'SELECT',
          'FROM',
          'WHERE',
          'JOIN',
          'LEFT JOIN',
          'INNER JOIN',
          'GROUP BY',
          'ORDER BY',
          'HAVING',
          'LIMIT',
          'WITH',
          'AS',
          'COUNT(*)',
          'SUM(',
          'AVG(',
          'MAX(',
          'MIN(',
          'DISTINCT',
        ].map((keyword) => ({
          label: keyword,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: keyword,
          range,
        }));
        return { suggestions: [...keywordSuggestions, ...tableSuggestions, ...columnSuggestions] };
      },
    });
  }

  private updateEditor(sql: string): void {
    this.editor?.setValue(sql);
  }

  private renderCharts(): void {
    this.renderBarChart();
    this.renderAreaChart();
    this.renderDonutChart();
    this.renderHeatmap();
  }

  private renderBarChart(): void {
    const host = this.barChart?.nativeElement;
    if (!host) {
      return;
    }
    const metric = this.analyticsDepartmentMetric;
    const data = this.departmentPerformance.slice(0, 8).map((row) => ({
      label: row.department_name,
      value: Number(row[metric] ?? 0)
    }));
    if (!data.length) {
      d3.select(host).selectAll('*').remove();
      return;
    }
    d3.select(host).selectAll('*').remove();
    const width = 560;
    const height = 300;
    const margin = { top: 16, right: 22, bottom: 26, left: 150 };
    const svg = d3.select(host).attr('viewBox', `0 0 ${width} ${height}`);
    const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d.value) || 1]).range([0, width - margin.left - margin.right]);
    const y = d3.scaleBand().domain(data.map((d) => d.label)).range([margin.top, height - margin.bottom]).padding(0.22);
    const gradient = svg.append('defs').append('linearGradient').attr('id', 'barGradient');
    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#312e81');
    gradient.append('stop').attr('offset', '55%').attr('stop-color', '#6366f1');
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#a78bfa');
    svg.append('g')
      .selectAll('text')
      .data(data)
      .join('text')
      .attr('x', 12)
      .attr('y', (d) => (y(d.label) ?? 0) + y.bandwidth() / 2 + 4)
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', 12)
      .text((d) => d.label);
    svg.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', 0)
      .attr('y', (d) => y(d.label) ?? 0)
      .attr('height', y.bandwidth())
      .attr('rx', 8)
      .attr('fill', 'url(#barGradient)')
      .attr('width', 0)
      .transition()
      .duration(760)
      .attr('width', (d) => x(d.value));
  }

  private renderAreaChart(): void {
    const host = this.areaChart?.nativeElement;
    if (!host) {
      return;
    }
    const metric = this.analyticsTrendMetric;
    const data = this.termTrends.map((row, index) => ({
      index,
      label: `${row.academic_year} ${row.term_name}`,
      value: Number(row[metric] ?? 0),
    }));
    if (!data.length) {
      d3.select(host).selectAll('*').remove();
      return;
    }
    d3.select(host).selectAll('*').remove();
    const width = 560;
    const height = 260;
    const x = d3.scaleLinear().domain([0, data.length - 1]).range([30, width - 24]);
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (point) => point.value) || 1])
      .nice()
      .range([height - 30, 18]);
    const svg = d3.select(host).attr('viewBox', `0 0 ${width} ${height}`);
    const area = d3.area<(typeof data)[number]>().x((d) => x(d.index)).y0(height - 30).y1((d) => y(d.value)).curve(d3.curveCatmullRom);
    const line = d3.line<(typeof data)[number]>().x((d) => x(d.index)).y((d) => y(d.value)).curve(d3.curveCatmullRom);
    svg.append('path').datum(data).attr('d', area).attr('fill', '#6366f1').attr('opacity', 0.18);
    const path = svg.append('path').datum(data).attr('d', line).attr('fill', 'none').attr('stroke', '#a78bfa').attr('stroke-width', 3);
    const length = (path.node() as SVGPathElement).getTotalLength();
    path.attr('stroke-dasharray', length).attr('stroke-dashoffset', length).transition().duration(900).attr('stroke-dashoffset', 0);
    svg.selectAll('circle').data(data).join('circle').attr('cx', (d) => x(d.index)).attr('cy', (d) => y(d.value)).attr('r', 0).attr('fill', '#4ade80').transition().delay(650).duration(300).attr('r', 4);
    svg
      .append('g')
      .attr('transform', `translate(0,${height - 26})`)
      .selectAll('text')
      .data(data)
      .join('text')
      .attr('x', (d) => x(d.index))
      .attr('y', 0)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', 10)
      .text((d) => d.label.replace('2025-26 ', ''));
  }

  private renderDonutChart(): void {
    const host = this.donutChart?.nativeElement;
    if (!host) {
      return;
    }
    const metric = this.analyticsMixMetric;
    const data = this.courseMix.map((row) => ({
      label: row.course_type,
      value: Number(row[metric] ?? 0),
    }));
    if (!data.length) {
      d3.select(host).selectAll('*').remove();
      return;
    }
    d3.select(host).selectAll('*').remove();
    const width = 280;
    const height = 260;
    const radius = 92;
    const svg = d3.select(host).attr('viewBox', `0 0 ${width} ${height}`).append('g').attr('transform', `translate(${width / 2},${height / 2})`);
    const pie = d3.pie<(typeof data)[number]>().value((d) => d.value).sort(null);
    const arc = d3.arc<d3.PieArcDatum<(typeof data)[number]>>().innerRadius(58).outerRadius(radius);
    svg.selectAll('path').data(pie(data)).join('path').attr('fill', (_d, i) => ['#6366f1', '#a78bfa', '#10b981', '#ef4444'][i]).transition().delay((_d, i) => i * 120).attrTween('d', (d) => {
      const interp = d3.interpolate({ ...d, endAngle: d.startAngle }, d);
      return (t) => arc(interp(t)) ?? '';
    });
    svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-primary)')
      .attr('font-size', 22)
      .attr('font-weight', 800)
      .text(this.courseMix.length.toString());
    svg
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', 24)
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', 11)
      .text('course types');
  }

  private renderHeatmap(): void {
    const host = this.heatmapChart?.nativeElement;
    if (!host) {
      return;
    }
    const data = Array.from({ length: 24 }, (_, hour) => {
      const point = this.queryActivity.find((entry) => entry.hour_of_day === hour);
      return {
        hour,
        value: point?.query_count ?? 0,
        latency: point?.avg_latency_ms ?? 0,
      };
    });
    d3.select(host).selectAll('*').remove();
    const svg = d3.select(host).attr('viewBox', '0 0 560 120');
    const color = d3.scaleLinear<string>().domain([0, d3.max(data, (d) => d.value) || 1]).range(['#111827', '#6366f1']);
    svg.selectAll('rect').data(data).join('rect')
      .attr('x', (d) => 18 + (d.hour % 12) * 42)
      .attr('y', (d) => 20 + Math.floor(d.hour / 12) * 38)
      .attr('width', 24)
      .attr('height', 24)
      .attr('rx', 6)
      .attr('fill', (d) => color(d.value))
      .attr('opacity', 0)
      .transition()
      .delay((d) => d.hour * 18)
      .attr('opacity', 1);
    svg.selectAll('text.hour').data(data).join('text')
      .attr('class', 'hour')
      .attr('x', (d) => 30 + (d.hour % 12) * 42)
      .attr('y', (d) => 58 + Math.floor(d.hour / 12) * 38)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', 10)
      .text((d) => d.hour.toString().padStart(2, '0'));
  }

  private showToast(type: Toast['type'], message: string): void {
    const toast = { id: ++this.toastId, type, message };
    this.toasts = [...this.toasts, toast];
    setTimeout(() => {
      this.toasts = this.toasts.filter((item) => item.id !== toast.id);
    }, 4000);
  }

  private triggerUniverse(): void {
    this.universeMode = true;
    this.queryResult = {
      sql: 'SELECT * FROM universe;',
      results: [],
      explanation: 'Error: Universe too large. Try a subquery.',
      execution_time: 42,
      tables_used: ['universe'],
      complexity_level: 'cosmic'
    };
    setTimeout(() => {
      void this.initMonaco().then(() => this.updateEditor(this.queryResult?.sql ?? ''));
    });
    this.showToast('info', 'Universe too large. Try a subquery.');
    gsap.fromTo('.results-grid', { scale: 1 }, { scale: 1.05, yoyo: true, repeat: 3, duration: 0.08 });
    setTimeout(() => (this.universeMode = false), 1800);
  }

  private trackKonami(key: string): void {
    const expected = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    this.konamiBuffer = [...this.konamiBuffer, key].slice(-expected.length);
    if (this.konamiBuffer.join('|').toLowerCase() === expected.join('|').toLowerCase()) {
      this.activateMatrixMode();
      this.unlockAchievement('konami', 'Konami unlocked', 'Found the matrix easter egg.');
    }
  }

  // ============================================================
  //  Streaming SQL typewriter
  // ============================================================
  private startSse(): void {
    this.currentStreamSource?.close();
    const source = new EventSource(
      `${this.apiBaseUrl}/query/stream?natural_language=${encodeURIComponent(this.naturalLanguage)}`
    );
    this.currentStreamSource = source;
    this.streamingSql = '';
    source.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as {
          token: string;
          stage: string;
          kind?: string;
        };
        this.streamTokens = [...this.streamTokens.slice(-4), payload.token];
        if (payload.kind === 'sql_chunk') {
          this.streamingSql += payload.token;
          void this.initMonaco().then(() => this.updateEditor(this.streamingSql));
        }
        if (payload.stage === 'complete') {
          source.close();
          this.currentStreamSource = null;
        }
      } catch {
        // ignore stream parse errors
      }
    };
    source.onerror = () => {
      source.close();
      this.currentStreamSource = null;
    };
  }

  // ============================================================
  //  Query plan visualization (D3 tree)
  // ============================================================
  loadQueryPlan(): void {
    if (!this.queryResult?.sql) {
      return;
    }
    this.planLoading = true;
    this.planError = '';
    this.http
      .post<ExplainResponse>(`${this.apiBaseUrl}/query/explain`, { sql: this.queryResult.sql })
      .subscribe({
        next: (response) => {
          this.planResponse = response;
          this.planLoading = false;
          setTimeout(() => this.renderPlanTree());
          this.unlockAchievement('explain', 'Plan whisperer', 'Inspected an EXPLAIN tree.');
        },
        error: (error: { error?: { detail?: string } }) => {
          this.planLoading = false;
          this.planError = error.error?.detail ?? 'EXPLAIN failed.';
          this.showToast('error', this.planError);
        },
      });
  }

  private renderPlanTree(): void {
    const host = this.planTree?.nativeElement;
    const root = this.planResponse?.plan;
    if (!host || !root) {
      return;
    }
    d3.select(host).selectAll('*').remove();

    const width = 760;
    const height = 380;
    const svg = d3.select(host).attr('viewBox', `0 0 ${width} ${height}`);
    const g = svg.append('g').attr('transform', 'translate(40,30)');

    type PlanHierarchy = { name: string; cost: number; rows: number; relation: string; children: PlanHierarchy[] };
    const toHierarchy = (node: PlanNode): PlanHierarchy => ({
      name: String(node['Node Type'] ?? 'Plan'),
      cost: Number(node['Total Cost'] ?? 0),
      rows: Number(node['Plan Rows'] ?? 0),
      relation: String(node['Relation Name'] ?? ''),
      children: (node.Plans ?? []).map(toHierarchy),
    });

    const layout = d3.tree<PlanHierarchy>().size([width - 100, height - 80]);
    const hierarchy = layout(d3.hierarchy<PlanHierarchy>(toHierarchy(root)));

    g.selectAll('path.link')
      .data(hierarchy.links())
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', 'rgba(167,139,250,0.4)')
      .attr('stroke-width', 1.6)
      .attr('d', (link) => {
        const source = link.source as { x: number; y: number };
        const target = link.target as { x: number; y: number };
        return `M${source.x},${source.y} C${source.x},${(source.y + target.y) / 2} ${target.x},${(source.y + target.y) / 2} ${target.x},${target.y}`;
      });

    const node = g
      .selectAll<SVGGElement, d3.HierarchyPointNode<PlanHierarchy>>('g.node')
      .data(hierarchy.descendants())
      .join('g')
      .attr('class', 'node')
      .attr('transform', (d) => `translate(${d.x},${d.y})`);

    node
      .append('rect')
      .attr('x', -78)
      .attr('y', -22)
      .attr('width', 156)
      .attr('height', 44)
      .attr('rx', 12)
      .attr('fill', 'rgba(99,102,241,0.18)')
      .attr('stroke', 'rgba(167,139,250,0.7)');

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', -4)
      .attr('fill', '#f1f5f9')
      .attr('font-size', 12)
      .attr('font-weight', 700)
      .text((d) => d.data.name);

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', 14)
      .attr('fill', '#94a3b8')
      .attr('font-size', 10)
      .text((d) => `cost ${d.data.cost.toFixed(0)} · ~${d.data.rows} rows`);
  }

  // ============================================================
  //  Auto-repair (Fix it)
  // ============================================================
  repairCurrentSql(): void {
    if (!this.queryResult?.sql) {
      return;
    }
    this.repairLoading = true;
    this.repairError = '';
    this.http
      .post<RepairResponse>(`${this.apiBaseUrl}/query/fixit`, {
        sql: this.queryResult.sql,
        error: this.errorMessage || 'manual repair request',
        natural_language: this.naturalLanguage,
      })
      .subscribe({
        next: (response) => {
          this.repairResponse = response;
          this.repairLoading = false;
          this.queryResult = {
            ...(this.queryResult as QueryResponse),
            sql: response.repaired_sql,
            results: response.results,
            explanation: response.explanation,
          };
          this.streamingSql = response.repaired_sql;
          setTimeout(() => {
            void this.initMonaco().then(() => this.updateEditor(response.repaired_sql));
            this.renderResultChart();
          });
          this.showToast('success', 'Query repaired');
          this.unlockAchievement('fixit', 'Bug squasher', 'Repaired a failing SQL query.');
        },
        error: (error: { error?: { detail?: string } }) => {
          this.repairLoading = false;
          this.repairError = error.error?.detail ?? 'Repair failed';
          this.showToast('error', this.repairError);
        },
      });
  }

  // ============================================================
  //  Voice query (Web Speech API + TTS)
  // ============================================================
  toggleVoiceInput(): void {
    if (!this.voiceSupported) {
      this.showToast('error', 'Voice input is not supported in this browser.');
      return;
    }
    if (this.voiceListening) {
      this.recognition?.stop();
      this.voiceListening = false;
      return;
    }
    type SpeechCtor = new () => {
      lang: string;
      continuous: boolean;
      interimResults: boolean;
      onresult: (event: { results: { isFinal: boolean; 0: { transcript: string } }[] }) => void;
      onend: () => void;
      onerror: () => void;
      start: () => void;
      stop: () => void;
    };
    const Ctor = ((window as unknown as { SpeechRecognition?: SpeechCtor; webkitSpeechRecognition?: SpeechCtor }).SpeechRecognition
      ?? (window as unknown as { webkitSpeechRecognition?: SpeechCtor }).webkitSpeechRecognition);
    if (!Ctor) {
      this.showToast('error', 'Voice not supported');
      return;
    }
    const recognition = new Ctor();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
      const transcript = Array.from({ length: event.results.length }, (_, i) => event.results[i][0].transcript).join(' ');
      this.naturalLanguage = transcript;
      const isFinal = Array.from({ length: event.results.length }, (_, i) => event.results[i].isFinal).some(Boolean);
      if (isFinal) {
        this.voiceListening = false;
        this.unlockAchievement('voice', 'Loud and clear', 'Used voice input.');
        this.submitQuery();
      }
    };
    recognition.onend = () => {
      this.voiceListening = false;
    };
    recognition.onerror = () => {
      this.voiceListening = false;
    };
    recognition.start();
    this.recognition = { stop: () => recognition.stop(), start: () => recognition.start() };
    this.voiceListening = true;
    this.showToast('info', 'Listening...');
  }

  speakExplanation(): void {
    if (!this.speechSynthSupported) {
      this.showToast('error', 'Text-to-speech is not supported here.');
      return;
    }
    const text = this.queryResult?.explanation;
    if (!text) {
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  // ============================================================
  //  Result chart auto-detect
  // ============================================================
  refreshChartConfig(): void {
    const rows = this.queryResult?.results ?? [];
    if (!rows.length) {
      this.showResultChart = false;
      return;
    }
    const columns = Object.keys(rows[0]);
    const numericColumns = columns.filter((col) =>
      rows.every((row) => row[col] === null || row[col] === '' || this.toNumericValue(row[col]) !== null)
    );
    const labelColumns = columns.filter((col) => !numericColumns.includes(col));
    if (!numericColumns.length || !labelColumns.length) {
      this.showResultChart = false;
      return;
    }
    const labelPriority = (column: string): number => {
      const normalized = column.toLowerCase();
      if (normalized.includes('name') || normalized.includes('title')) {
        return 0;
      }
      if (normalized.includes('department') || normalized.includes('course') || normalized.includes('term')) {
        return 1;
      }
      if (normalized.includes('code')) {
        return 3;
      }
      if (normalized.includes('roll_number') || normalized.endsWith('_id') || normalized === 'id') {
        return 4;
      }
      return 2;
    };
    const valuePriority = (column: string): number => {
      const normalized = column.toLowerCase();
      if (normalized.includes('count') || normalized.includes('total') || normalized.includes('avg')) {
        return 0;
      }
      if (normalized.includes('cgpa') || normalized.includes('gpa') || normalized.includes('score') || normalized.includes('amount')) {
        return 1;
      }
      if (normalized.includes('rank')) {
        return 3;
      }
      return 2;
    };
    this.chartLabelColumn = [...labelColumns].sort((left, right) => labelPriority(left) - labelPriority(right))[0];
    this.chartValueColumn = [...numericColumns].sort((left, right) => valuePriority(left) - valuePriority(right))[0];
    this.showResultChart = true;
  }

  setChartType(type: ChartType): void {
    this.chartType = type;
    this.renderResultChart();
  }

  setChartLabelColumn(column: string): void {
    this.chartLabelColumn = column;
    this.renderResultChart();
  }

  setChartValueColumn(column: string): void {
    this.chartValueColumn = column;
    this.renderResultChart();
  }

  refreshAnalyticsVisuals(): void {
    this.renderCharts();
  }

  private renderResultChart(): void {
    const host = this.resultChart?.nativeElement;
    const rows = this.queryResult?.results ?? [];
    if (!host || !this.showResultChart || !rows.length) {
      return;
    }
    const labelKey = this.chartLabelColumn;
    const valueKey = this.chartValueColumn;
    const rawData = rows
      .slice(0, 24)
      .map((row) => ({
        label: this.formatChartLabel(row[labelKey]),
        fullLabel: String(row[labelKey] ?? ''),
        value: this.toNumericValue(row[valueKey]) ?? 0,
      }))
      .filter((point) => Number.isFinite(point.value));
    const data = this.aggregateChartData(rawData);
    d3.select(host).selectAll('*').remove();
    const width = 600;
    const height = 280;
    const svg = d3.select(host).attr('viewBox', `0 0 ${width} ${height}`);
    const values = data.map((point) => point.value);
    const minValue = d3.min(values) ?? 0;
    const maxValue = d3.max(values) ?? 1;
    const useTightDomain = minValue > 0 && maxValue > minValue && (maxValue - minValue) / maxValue < 0.35;
    const yDomainMin = useTightDomain ? Math.max(0, minValue - (maxValue - minValue) * 0.25) : 0;

    if (this.chartType === 'bar') {
      const margin = { top: 16, right: 18, bottom: 38, left: 60 };
      const x = d3
        .scaleBand()
        .domain(data.map((d) => d.label))
        .range([margin.left, width - margin.right])
        .padding(0.18);
      const y = d3
        .scaleLinear()
        .domain([yDomainMin, maxValue || 1])
        .nice()
        .range([height - margin.bottom, margin.top]);
      svg
        .append('g')
        .attr('transform', `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x).tickSizeOuter(0))
        .selectAll('text')
        .attr('fill', 'var(--text-secondary)')
        .attr('font-size', 10)
        .attr('transform', 'rotate(-22)')
        .style('text-anchor', 'end')
        .append('title')
        .text((_value, index) => data[index]?.fullLabel ?? '');
      svg
        .append('g')
        .attr('transform', `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).ticks(5))
        .selectAll('text')
        .attr('fill', 'var(--text-secondary)');
      svg
        .selectAll('rect.bar')
        .data(data)
        .join('rect')
        .attr('class', 'bar')
        .attr('x', (d) => x(d.label) ?? 0)
        .attr('width', x.bandwidth())
        .attr('y', y(yDomainMin))
        .attr('height', 0)
        .attr('rx', 6)
        .attr('fill', '#a78bfa')
        .transition()
        .duration(620)
        .attr('y', (d) => y(d.value))
        .attr('height', (d) => Math.max(0, y(yDomainMin) - y(d.value)));
    } else if (this.chartType === 'line') {
      const margin = { top: 16, right: 18, bottom: 38, left: 50 };
      const x = d3
        .scalePoint()
        .domain(data.map((d) => d.label))
        .range([margin.left, width - margin.right]);
      const y = d3
        .scaleLinear()
        .domain([yDomainMin, maxValue || 1])
        .nice()
        .range([height - margin.bottom, margin.top]);
      const line = d3
        .line<{ label: string; value: number }>()
        .x((d) => x(d.label) ?? 0)
        .y((d) => y(d.value))
        .curve(d3.curveCatmullRom);
      svg
        .append('g')
        .attr('transform', `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('fill', 'var(--text-secondary)')
        .attr('font-size', 10)
        .attr('transform', 'rotate(-22)')
        .style('text-anchor', 'end')
        .append('title')
        .text((_value, index) => data[index]?.fullLabel ?? '');
      svg
        .append('g')
        .attr('transform', `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).ticks(5))
        .selectAll('text')
        .attr('fill', 'var(--text-secondary)');
      svg
        .append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', '#6366f1')
        .attr('stroke-width', 3)
        .attr('d', line);
      svg
        .selectAll('circle.point')
        .data(data)
        .join('circle')
        .attr('class', 'point')
        .attr('cx', (d) => x(d.label) ?? 0)
        .attr('cy', (d) => y(d.value))
        .attr('r', 4)
        .attr('fill', '#a78bfa');
    } else {
      const pieData = this.limitPieSlices(data, 8);
      const radius = Math.min(width, height) / 2 - 28;
      const g = svg.append('g').attr('transform', `translate(${width / 2},${height / 2})`);
      const pie = d3
        .pie<{ label: string; fullLabel: string; value: number }>()
        .sort((left, right) => right.value - left.value)
        .value((d) => d.value);
      const arc = d3
        .arc<d3.PieArcDatum<{ label: string; fullLabel: string; value: number }>>()
        .innerRadius(radius * 0.58)
        .outerRadius(radius)
        .cornerRadius(8);
      const outerArc = d3
        .arc<d3.PieArcDatum<{ label: string; fullLabel: string; value: number }>>()
        .innerRadius(radius * 1.08)
        .outerRadius(radius * 1.08);
      const palette = ['#6366f1', '#a78bfa', '#10b981', '#ef4444', '#f59e0b', '#22d3ee', '#ec4899', '#84cc16'];
      const arcs = pie(pieData);
      const total = d3.sum(pieData, (d) => d.value);

      g.selectAll('path')
        .data(arcs)
        .join('path')
        .attr('d', arc)
        .attr('fill', (_d, i) => palette[i % palette.length])
        .attr('stroke', 'rgba(8, 8, 13, 0.9)')
        .attr('stroke-width', 2)
        .attr('opacity', 0.94)
        .append('title')
        .text((d) => `${d.data.fullLabel}: ${d.data.value}`);

      g.append('circle')
        .attr('r', radius * 0.43)
        .attr('fill', 'rgba(8, 8, 13, 0.96)')
        .attr('stroke', 'rgba(167, 139, 250, 0.18)');

      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('y', -6)
        .attr('fill', '#f8fafc')
        .attr('font-size', 24)
        .attr('font-weight', 800)
        .text(this.formatChartValue(total));

      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('y', 18)
        .attr('fill', '#94a3b8')
        .attr('font-size', 11)
        .text(this.chartValueColumn);

      if (pieData.length <= 6) {
        g.selectAll('polyline')
          .data(arcs)
          .join('polyline')
          .attr('fill', 'none')
          .attr('stroke', 'rgba(148, 163, 184, 0.65)')
          .attr('stroke-width', 1.2)
          .attr('points', (d) => {
            const start = arc.centroid(d);
            const middle = outerArc.centroid(d);
            const end = [...middle] as [number, number];
            end[0] += end[0] > 0 ? 28 : -28;
            return [start, middle, end].map((point) => point.join(',')).join(' ');
          });

        g.selectAll('text.slice-label')
          .data(arcs)
          .join('text')
          .attr('class', 'slice-label')
          .attr('transform', (d) => {
            const point = outerArc.centroid(d);
            point[0] += point[0] > 0 ? 34 : -34;
            return `translate(${point[0]},${point[1]})`;
          })
          .attr('text-anchor', (d) => (outerArc.centroid(d)[0] > 0 ? 'start' : 'end'))
          .attr('fill', '#e2e8f0')
          .attr('font-size', 10)
          .attr('font-weight', 700)
          .text((d) => `${d.data.label} ${((d.data.value / total) * 100).toFixed(0)}%`);
      }
    }
  }

  private toNumericValue(value: unknown): number | null {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === 'string' && value.trim()) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
  }

  private formatChartLabel(value: unknown): string {
    const label = String(value ?? '');
    return label.length > 16 ? `${label.slice(0, 13)}...` : label;
  }

  private aggregateChartData(data: { label: string; fullLabel: string; value: number }[]): { label: string; fullLabel: string; value: number }[] {
    const buckets = new Map<string, { label: string; fullLabel: string; value: number }>();
    for (const entry of data) {
      const key = entry.fullLabel;
      const existing = buckets.get(key);
      if (existing) {
        existing.value += entry.value;
      } else {
        buckets.set(key, { ...entry });
      }
    }
    return [...buckets.values()];
  }

  private limitPieSlices(data: { label: string; fullLabel: string; value: number }[], maxSlices: number): { label: string; fullLabel: string; value: number }[] {
    const sorted = [...data].sort((left, right) => right.value - left.value);
    if (sorted.length <= maxSlices) {
      return sorted;
    }
    const top = sorted.slice(0, maxSlices - 1);
    const rest = sorted.slice(maxSlices - 1);
    const otherValue = d3.sum(rest, (item) => item.value);
    return [
      ...top,
      {
        label: 'Other',
        fullLabel: rest.map((item) => item.fullLabel).join(', '),
        value: otherValue,
      },
    ];
  }

  private formatChartValue(value: number): string {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}k`;
    }
    if (value % 1 !== 0) {
      return value.toFixed(2);
    }
    return value.toString();
  }

  // ============================================================
  //  Result export (CSV / JSON / Markdown / Pandas)
  // ============================================================
  exportResults(format: 'csv' | 'json' | 'markdown' | 'pandas'): void {
    const rows = this.queryResult?.results ?? [];
    if (!rows.length) {
      this.showToast('info', 'Nothing to export.');
      return;
    }
    const columns = Object.keys(rows[0]);
    let content = '';
    let extension = 'txt';
    let mime = 'text/plain';
    if (format === 'csv') {
      const escape = (value: unknown) => {
        const text = value === null || value === undefined ? '' : String(value);
        return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
      };
      content = [columns.join(','), ...rows.map((row) => columns.map((col) => escape(row[col])).join(','))].join('\n');
      extension = 'csv';
      mime = 'text/csv';
    } else if (format === 'json') {
      content = JSON.stringify(rows, null, 2);
      extension = 'json';
      mime = 'application/json';
    } else if (format === 'markdown') {
      const header = `| ${columns.join(' | ')} |`;
      const divider = `| ${columns.map(() => '---').join(' | ')} |`;
      const body = rows
        .map((row) => `| ${columns.map((col) => String(row[col] ?? '').replace(/\|/g, '\\|')).join(' | ')} |`)
        .join('\n');
      content = `${header}\n${divider}\n${body}`;
      extension = 'md';
      mime = 'text/markdown';
    } else {
      content = `import pandas as pd\n\nsql = """${this.queryResult?.sql ?? ''}"""\n# Connect with: engine = sqlalchemy.create_engine('postgresql://...')\ndf = pd.read_sql(sql, engine)\nprint(df.head())`;
      extension = 'py';
      mime = 'text/x-python';
    }

    if (format === 'pandas') {
      void navigator.clipboard.writeText(content);
      this.showToast('success', 'Pandas snippet copied');
      this.unlockAchievement('pandas-export', 'Pandas pilot', 'Copied a Pandas snippet.');
      return;
    }
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `querymind-results.${extension}`;
    link.click();
    URL.revokeObjectURL(url);
    this.unlockAchievement(`export-${format}`, 'Data exporter', `Exported results as ${format.toUpperCase()}.`);
    this.showToast('success', `Exported as ${format.toUpperCase()}`);
  }

  // ============================================================
  //  Live metrics strip
  // ============================================================
  loadMetrics(): void {
    this.http.get<MetricsResponse>(`${this.apiBaseUrl}/metrics`).subscribe({
      next: (response) => {
        this.metrics = response;
      },
      error: () => {
        // metrics are non-critical
      },
    });
  }

  // ============================================================
  //  Saved queries + share links
  // ============================================================
  loadSavedQueries(): void {
    try {
      const stored = localStorage.getItem('querymind-saved-queries');
      this.savedQueries = stored ? (JSON.parse(stored) as SavedQuery[]) : [];
    } catch {
      this.savedQueries = [];
    }
  }

  saveCurrentQuery(): void {
    if (!this.queryResult) {
      this.showToast('info', 'Run a query before saving.');
      return;
    }
    const entry: SavedQuery = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      label: this.naturalLanguage.slice(0, 80),
      natural_language: this.naturalLanguage,
      sql: this.queryResult.sql,
      saved_at: Date.now(),
    };
    this.savedQueries = [entry, ...this.savedQueries.filter((item) => item.sql !== entry.sql)].slice(0, 24);
    localStorage.setItem('querymind-saved-queries', JSON.stringify(this.savedQueries));
    this.showToast('success', 'Query saved');
    this.unlockAchievement('saved', 'Bookmark fan', 'Saved your first query.');
  }

  loadSavedQuery(entry: SavedQuery): void {
    this.naturalLanguage = entry.natural_language;
    this.setTab('query');
    this.submitQuery();
  }

  removeSavedQuery(id: string): void {
    this.savedQueries = this.savedQueries.filter((item) => item.id !== id);
    localStorage.setItem('querymind-saved-queries', JSON.stringify(this.savedQueries));
  }

  updateShareLink(): void {
    if (!this.queryResult?.query_log_id) {
      this.shareLink = '';
      return;
    }
    const url = new URL(window.location.href);
    url.searchParams.set('q', String(this.queryResult.query_log_id));
    this.shareLink = url.toString();
  }

  copyShareLink(): void {
    if (!this.shareLink) {
      this.updateShareLink();
    }
    if (!this.shareLink) {
      this.showToast('info', 'Run a query first.');
      return;
    }
    void navigator.clipboard.writeText(this.shareLink);
    this.showToast('success', 'Share link copied');
  }

  private hydrateFromShareLink(): void {
    try {
      const params = new URLSearchParams(window.location.search);
      const id = params.get('q');
      if (!id) {
        return;
      }
      this.http.get<HistoryItem>(`${this.apiBaseUrl}/history/${encodeURIComponent(id)}`).subscribe({
        next: (item) => {
          this.naturalLanguage = item.user_input;
          this.queryResult = {
            sql: item.generated_sql,
            results: [],
            explanation: item.explanation,
            execution_time: item.execution_time_ms,
            tables_used: [],
            complexity_level: 'shared',
            query_log_id: item.id,
          };
          this.launched = true;
          this.activeTab = 'query';
          setTimeout(() => {
            void this.initMonaco().then(() => this.updateEditor(item.generated_sql));
          });
          this.showToast('info', 'Loaded shared query');
        },
        error: () => {
          this.showToast('error', 'Shared query not found.');
        },
      });
    } catch {
      // ignore
    }
  }

  // ============================================================
  //  Achievements
  // ============================================================
  loadAchievements(): void {
    try {
      const stored = localStorage.getItem('querymind-achievements');
      this.achievements = stored ? (JSON.parse(stored) as Achievement[]) : [];
    } catch {
      this.achievements = [];
    }
  }

  unlockAchievement(id: string, title: string, hint: string): void {
    if (this.achievements.some((entry) => entry.id === id)) {
      return;
    }
    const achievement: Achievement = { id, title, hint, unlocked_at: Date.now() };
    this.achievements = [achievement, ...this.achievements].slice(0, 32);
    localStorage.setItem('querymind-achievements', JSON.stringify(this.achievements));
    this.showToast('success', `Achievement: ${title}`);
  }

  private handleQueryAchievements(response: QueryResponse): void {
    this.unlockAchievement('first-query', 'First query', 'Submitted a natural language query.');
    if (response.tables_used.length >= 3) {
      this.unlockAchievement('multi-join', 'Joiner', 'Ran a query that joined 3+ tables.');
    }
    if (this.metrics.total_queries >= 9) {
      this.unlockAchievement('streaker', 'On a streak', 'Ran 10 queries in QueryMind.');
    }
  }

  // ============================================================
  //  Matrix rain mode
  // ============================================================
  activateMatrixMode(): void {
    if (this.matrixModeActive) {
      return;
    }
    this.matrixModeActive = true;
    document.body.classList.add('matrix-mode');
    setTimeout(() => this.runMatrixCanvas(), 0);
    setTimeout(() => this.deactivateMatrixMode(), 6500);
  }

  private deactivateMatrixMode(): void {
    this.matrixModeActive = false;
    document.body.classList.remove('matrix-mode');
    cancelAnimationFrame(this.matrixFrame);
  }

  private runMatrixCanvas(): void {
    const canvas = this.matrixCanvas?.nativeElement;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext('2d');
    if (!context) {
      return;
    }
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const fontSize = 18;
    const columns = Math.floor(canvas.width / fontSize);
    const drops = Array.from({ length: columns }, () => Math.random() * -50);
    const glyphs = 'SELECT JOIN WHERE GROUP BY ROLLUP CUBE WITH RECURSIVE INDEX TRANSACTION ACID 0123456789'.split('');

    const draw = () => {
      if (!this.matrixModeActive) {
        return;
      }
      context.fillStyle = 'rgba(2,6,12,0.18)';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.fillStyle = '#4ade80';
      context.font = `${fontSize}px JetBrains Mono, monospace`;
      drops.forEach((value, index) => {
        const text = glyphs[Math.floor(Math.random() * glyphs.length)];
        context.fillText(text, index * fontSize, value * fontSize);
        if (value * fontSize > canvas.height && Math.random() > 0.965) {
          drops[index] = 0;
        }
        drops[index] += 1;
      });
      this.matrixFrame = requestAnimationFrame(draw);
    };
    draw();
  }
}
