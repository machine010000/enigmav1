import type { LanguageCode } from "./config";

type FreelancingCopy = {
  title: string;
  intro: string;
  loading: string;
  error: string;
  retry: string;
  empty: string;
  connected: string;
  notConnected: string;
  pending: string;
  reserved: string;
  marketplace: string;
  jobs: string;
  verification: string;
  provider: string;
  capabilities: string;
  academy: string;
  creativity: string;
  decision: string;
  applications: string;
  activeWork: string;
  noProvider: string;
  noAssessment: string;
  assess: string;
  assessing: string;
  project: string;
  budget: string;
  description: string;
  skills: string;
  status: string;
  recommendation: string;
  readiness: string;
  blockers: string;
  missing: string;
  plan: string;
  generatePlan: string;
  planLoading: string;
  planReady: string;
  backToJobs: string;
  noData: string;
};

export const freelancingCopy: Record<LanguageCode, FreelancingCopy> = {
  en: { title: "Freelancing Control Center", intro: "A verified path from opportunity intake to an evidence-based capability decision.", loading: "Loading backend workspace...", error: "Unable to load freelancing data.", retry: "Retry", empty: "No opportunities are currently available from connected sources.", connected: "Connected", notConnected: "Not connected", pending: "Backend integration pending", reserved: "Reserved", marketplace: "Marketplace / Jobs", jobs: "Jobs", verification: "Opportunity Verification", provider: "Provider Intelligence", capabilities: "Capability Check", academy: "Academy handoff", creativity: "Creativity", decision: "Brain Decision", applications: "Applications", activeWork: "Active Work", noProvider: "Provider intelligence is unavailable from the current source.", noAssessment: "No capability assessment has been run yet.", assess: "Assess opportunity", assessing: "Assessing...", project: "Project", budget: "Budget", description: "Description", skills: "Skills / requirements", status: "Current status", recommendation: "Backend recommendation", readiness: "Readiness", blockers: "Blockers", missing: "Missing capabilities", plan: "Training / development", generatePlan: "Generate development plan", planLoading: "Generating...", planReady: "Development plan returned by backend.", backToJobs: "Back to jobs", noData: "No backend data returned." },
  ar: { title: "مركز التحكم بالعمل الحر", intro: "مسار موثق من استقبال الفرصة إلى قرار القدرات المبني على الأدلة.", loading: "جار تحميل مساحة العمل...", error: "تعذر تحميل بيانات العمل الحر.", retry: "إعادة المحاولة", empty: "لا توجد فرص متاحة حالياً من المصادر المتصلة.", connected: "متصل", notConnected: "غير متصل", pending: "تكامل الواجهة الخلفية قيد الانتظار", reserved: "محجوز", marketplace: "السوق والوظائف", jobs: "الوظائف", verification: "التحقق من الفرصة", provider: "معلومات العميل", capabilities: "فحص القدرات", academy: "إحالة الأكاديمية", creativity: "الإبداع", decision: "قرار الدماغ", applications: "الطلبات", activeWork: "العمل النشط", noProvider: "معلومات العميل غير متاحة من المصدر الحالي.", noAssessment: "لم يجر تقييم القدرات بعد.", assess: "تقييم الفرصة", assessing: "جار التقييم...", project: "المشروع", budget: "الميزانية", description: "الوصف", skills: "المهارات والمتطلبات", status: "الحالة الحالية", recommendation: "توصية الواجهة الخلفية", readiness: "الجاهزية", blockers: "العوائق", missing: "القدرات المفقودة", plan: "التطوير والتدريب", generatePlan: "إنشاء خطة تطوير", planLoading: "جار الإنشاء...", planReady: "أعادت الواجهة الخلفية خطة التطوير.", backToJobs: "العودة إلى الوظائف", noData: "لم تعد الواجهة الخلفية ببيانات." },
  es: { title: "Centro de control freelance", intro: "Un camino verificado desde la oportunidad hasta una decisión de capacidades basada en evidencia.", loading: "Cargando espacio de trabajo...", error: "No se pudieron cargar los datos freelance.", retry: "Reintentar", empty: "No hay oportunidades disponibles de fuentes conectadas.", connected: "Conectado", notConnected: "No conectado", pending: "Integración backend pendiente", reserved: "Reservado", marketplace: "Mercado / Trabajos", jobs: "Trabajos", verification: "Verificación de oportunidad", provider: "Información del cliente", capabilities: "Comprobación de capacidades", academy: "Enlace con Academia", creativity: "Creatividad", decision: "Decisión del Brain", applications: "Solicitudes", activeWork: "Trabajo activo", noProvider: "La información del cliente no está disponible en la fuente actual.", noAssessment: "Aún no se ha ejecutado una evaluación.", assess: "Evaluar oportunidad", assessing: "Evaluando...", project: "Proyecto", budget: "Presupuesto", description: "Descripción", skills: "Habilidades / requisitos", status: "Estado actual", recommendation: "Recomendación del backend", readiness: "Preparación", blockers: "Bloqueos", missing: "Capacidades faltantes", plan: "Desarrollo / formación", generatePlan: "Generar plan de desarrollo", planLoading: "Generando...", planReady: "El backend devolvió un plan de desarrollo.", backToJobs: "Volver a trabajos", noData: "El backend no devolvió datos." },
  fr: { title: "Centre de contrôle freelance", intro: "Un parcours vérifié de l’opportunité à une décision de capacité fondée sur les preuves.", loading: "Chargement de l’espace de travail...", error: "Impossible de charger les données freelance.", retry: "Réessayer", empty: "Aucune opportunité disponible depuis les sources connectées.", connected: "Connecté", notConnected: "Non connecté", pending: "Intégration backend en attente", reserved: "Réservé", marketplace: "Marché / Missions", jobs: "Missions", verification: "Vérification de l’opportunité", provider: "Informations client", capabilities: "Vérification des capacités", academy: "Passerelle Académie", creativity: "Créativité", decision: "Décision du Brain", applications: "Candidatures", activeWork: "Travail actif", noProvider: "Les informations client ne sont pas disponibles depuis la source actuelle.", noAssessment: "Aucune évaluation de capacité n’a encore été lancée.", assess: "Évaluer l’opportunité", assessing: "Évaluation...", project: "Projet", budget: "Budget", description: "Description", skills: "Compétences / exigences", status: "État actuel", recommendation: "Recommandation du backend", readiness: "Préparation", blockers: "Blocages", missing: "Capacités manquantes", plan: "Développement / formation", generatePlan: "Générer un plan de développement", planLoading: "Génération...", planReady: "Le backend a renvoyé un plan de développement.", backToJobs: "Retour aux missions", noData: "Le backend n’a renvoyé aucune donnée." },
};
