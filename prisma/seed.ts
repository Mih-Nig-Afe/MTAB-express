/**
 * Prisma seed — 2 years of realistic mock parcel data for dashboard testing.
 *
 * Prerequisites (run once via Python seeds inside Docker):
 *   docker compose -f docker-compose.dev.yml exec api python scripts/seed_branches.py
 *   docker compose -f docker-compose.dev.yml exec api python scripts/seed_admin.py
 *
 * Local run (host → Postgres on 5433):
 *   DATABASE_URL="postgresql://mela:mela@localhost:5433/mela_express" npm run db:seed:mock
 *
 * Re-seed from scratch:
 *   MOCK_RESET=1 DATABASE_URL="..." npm run db:seed:mock
 */
import { randomUUID } from 'crypto';
import { faker } from '@faker-js/faker';
import {
  PrismaClient,
  type parcel_status_enum,
  type payment_mode_enum,
  type payment_method_enum,
  type payment_status_enum,
  type content_category_enum,
  type size_category_enum,
} from '@prisma/client';

const prisma = new PrismaClient();

const MOCK_PREFIX = `${(process.env.TRACKING_PREFIX || process.env.BRAND_SHORT || 'MK').toUpperCase()}-MK-`;
const BRANCH_CODES = ['HW', 'AA1', 'AA2', 'AA3', 'AA4', 'AD', 'DD', 'JJ'];
const CONTENT_CATS: content_category_enum[] = [
  'documents',
  'electronics',
  'clothing',
  'food',
  'fragile',
  'general',
];
const SIZE_CATS: size_category_enum[] = ['small', 'medium', 'large', 'oversized'];

const STATUS_CHAIN: parcel_status_enum[] = [
  'created',
  'received_at_origin',
  'processed_at_origin',
  'dispatched_from_origin',
  'in_transit',
  'arrived_origin_airport',
  'checked_in_flight',
  'departed',
  'arrived_destination_airport',
  'released_from_airport',
  'arrived_at_destination',
  'distributed_to_branch',
  'ready_for_pickup',
  'delivered',
];

const TERMINAL: parcel_status_enum[] = [
  'delivered',
  'returned',
  'cancelled',
  'lost',
  'on_hold',
];

const YEARS = parseInt(process.env.MOCK_YEARS ?? '2', 10);
const MIN_PER_DAY = parseInt(process.env.MOCK_MIN_PER_DAY ?? '6', 10);
const MAX_PER_DAY = parseInt(process.env.MOCK_MAX_PER_DAY ?? '14', 10);
const RESET = process.env.MOCK_RESET === '1';
const BATCH = 400;

faker.seed(42);

function utcDate(y: number, m: number, d: number, h = 0, min = 0): Date {
  return new Date(Date.UTC(y, m - 1, d, h, min));
}

function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setUTCDate(x.getUTCDate() + n);
  return x;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function pickWeighted<T extends string>(opts: [T, number][]): T {
  const total = opts.reduce((s, [, w]) => s + w, 0);
  let r = Math.random() * total;
  for (const [val, w] of opts) {
    r -= w;
    if (r <= 0) return val;
  }
  return opts[opts.length - 1][0];
}

function finalStatus(ageDays: number): parcel_status_enum {
  if (ageDays > 90) {
    return pickWeighted([
      ['delivered', 0.82],
      ['cancelled', 0.06],
      ['returned', 0.04],
      ['lost', 0.02],
      ['on_hold', 0.06],
    ]);
  }
  if (ageDays > 30) {
    return pickWeighted([
      ['delivered', 0.55],
      ['ready_for_pickup', 0.12],
      ['in_transit', 0.1],
      ['distributed_to_branch', 0.08],
      ['cancelled', 0.05],
      ['on_hold', 0.1],
    ]);
  }
  if (ageDays > 7) {
    return pickWeighted([
      ['in_transit', 0.28],
      ['ready_for_pickup', 0.18],
      ['delivered', 0.22],
      ['received_at_origin', 0.12],
      ['processed_at_origin', 0.1],
      ['on_hold', 0.1],
    ]);
  }
  return pickWeighted([
    ['created', 0.35],
    ['received_at_origin', 0.3],
    ['processed_at_origin', 0.2],
    ['in_transit', 0.15],
  ]);
}

function historyForStatus(
  final: parcel_status_enum,
  createdAt: Date,
  adminId: string,
  branchId: string,
  parcelId: string,
) {
  if (TERMINAL.includes(final) && final !== 'delivered') {
    const steps: parcel_status_enum[] = ['created', 'received_at_origin', final];
    return steps.map((st, i) => ({
      id: randomUUID(),
      parcel_id: parcelId,
      from_status: i === 0 ? null : steps[i - 1],
      to_status: st,
      changed_by: adminId,
      branch_id: branchId,
      note: `Mock seed — ${st.replace(/_/g, ' ')}`,
      timestamp: new Date(createdAt.getTime() + i * 6 * 3600_000),
    }));
  }

  const idx = STATUS_CHAIN.indexOf(final);
  const chain = idx >= 0 ? STATUS_CHAIN.slice(0, idx + 1) : (['created', final] as parcel_status_enum[]);
  return chain.map((st, i) => ({
    id: randomUUID(),
    parcel_id: parcelId,
    from_status: i === 0 ? null : chain[i - 1],
    to_status: st,
    changed_by: adminId,
    branch_id: branchId,
    note: `Mock seed — ${st.replace(/_/g, ' ')}`,
    timestamp: new Date(createdAt.getTime() + i * 8 * 3600_000),
  }));
}

function parcelsPerDay(date: Date): number {
  const dow = date.getUTCDay();
  const weekend = dow === 0 || dow === 6 ? 0.65 : 1;
  const base = MIN_PER_DAY + Math.floor(Math.random() * (MAX_PER_DAY - MIN_PER_DAY + 1));
  return Math.max(2, Math.round(base * weekend));
}

async function clearMockData() {
  const mockParcels = await prisma.parcels.findMany({
    where: { tracking_code: { startsWith: MOCK_PREFIX } },
    select: { id: true },
  });
  const ids = mockParcels.map((p) => p.id);
  if (!ids.length) {
    console.log('No mock parcels to clear.');
    return;
  }
  console.log(`Clearing ${ids.length} mock parcels…`);
  await prisma.payments.deleteMany({ where: { parcel_id: { in: ids } } });
  await prisma.parcel_status_history.deleteMany({ where: { parcel_id: { in: ids } } });
  await prisma.parcel_journey_events.deleteMany({ where: { parcel_id: { in: ids } } });
  await prisma.parcels.deleteMany({ where: { id: { in: ids } } });
  await prisma.customers.deleteMany({ where: { phone: { startsWith: '+251970' } } });
  console.log('Mock data cleared.');
}

async function ensureCustomers(count: number): Promise<Map<string, string>> {
  const map = new Map<string, string>();
  const existing = await prisma.customers.findMany({
    where: { phone: { startsWith: '+251970' } },
    select: { id: true, phone: true },
  });
  for (const c of existing) map.set(c.phone, c.id);

  const toCreate: { id: string; phone: string; name: string; language: string }[] = [];
  for (let i = map.size; i < count; i++) {
    const phone = `+251970${String(i).padStart(6, '0')}`;
    if (map.has(phone)) continue;
    toCreate.push({
      id: randomUUID(),
      phone,
      name: faker.person.fullName(),
      language: Math.random() > 0.4 ? 'am' : 'en',
    });
  }
  if (toCreate.length) {
    await prisma.customers.createMany({ data: toCreate, skipDuplicates: true });
    for (const c of toCreate) map.set(c.phone, c.id);
  }
  return map;
}

async function main() {
  const dbUrl = process.env.DATABASE_URL ?? '';
  if (!dbUrl.startsWith('postgresql://')) {
    console.error(
      'Set DATABASE_URL to a Prisma-compatible URL, e.g.\n' +
        '  postgresql://mela:mela@localhost:5433/mela_express',
    );
    process.exit(1);
  }

  if (RESET) await clearMockData();

  const existingMock = await prisma.parcels.count({
    where: { tracking_code: { startsWith: MOCK_PREFIX } },
  });
  if (existingMock > 0 && !RESET) {
    console.log(
      `${existingMock} mock parcels already exist. Set MOCK_RESET=1 to replace them.`,
    );
    return;
  }

  const admin = await prisma.staff_users.findFirst({
    where: { phone: '+251900000000' },
  });
  if (!admin) {
    console.error('Admin not found. Run: docker compose exec api python scripts/seed_admin.py');
    process.exit(1);
  }

  const branches = await prisma.branches.findMany({
    where: { code: { in: BRANCH_CODES } },
  });
  const branchByCode = new Map(branches.map((b) => [b.code, b]));
  if (branchByCode.size < BRANCH_CODES.length) {
    console.error('Branches missing. Run: docker compose exec api python scripts/seed_branches.py');
    process.exit(1);
  }

  const customers = await ensureCustomers(120);
  const customerIds = [...customers.values()];
  const customerPhones = [...customers.keys()];

  const end = new Date();
  end.setUTCHours(0, 0, 0, 0);
  const start = addDays(end, -YEARS * 365);

  type ParcelRow = Parameters<typeof prisma.parcels.createMany>[0]['data'][number];
  type HistoryRow = Parameters<typeof prisma.parcel_status_history.createMany>[0]['data'][number];
  type PaymentRow = Parameters<typeof prisma.payments.createMany>[0]['data'][number];

  let parcelBatch: ParcelRow[] = [];
  let historyBatch: HistoryRow[] = [];
  let paymentBatch: PaymentRow[] = [];
  let totalParcels = 0;
  let seq = 0;

  const flush = async () => {
    if (parcelBatch.length) {
      await prisma.parcels.createMany({ data: parcelBatch, skipDuplicates: true });
      parcelBatch = [];
    }
    if (historyBatch.length) {
      await prisma.parcel_status_history.createMany({ data: historyBatch });
      historyBatch = [];
    }
    if (paymentBatch.length) {
      await prisma.payments.createMany({ data: paymentBatch, skipDuplicates: true });
      paymentBatch = [];
    }
  };

  console.log(`Generating ~${YEARS} year(s) of mock parcels (${start.toISOString().slice(0, 10)} → ${end.toISOString().slice(0, 10)})…`);

  for (let day = new Date(start); day <= end; day = addDays(day, 1)) {
    const count = parcelsPerDay(day);
    const ageDays = Math.floor((end.getTime() - day.getTime()) / 86400_000);

    for (let i = 0; i < count; i++) {
      seq += 1;
      const originCode = pick(BRANCH_CODES);
      let destCode = pick(BRANCH_CODES);
      while (destCode === originCode) destCode = pick(BRANCH_CODES);

      const origin = branchByCode.get(originCode)!;
      const dest = branchByCode.get(destCode)!;
      const senderId = pick(customerIds);
      const senderPhone = customerPhones[customerIds.indexOf(senderId)] ?? pick(customerPhones);

      const hour = 8 + Math.floor(Math.random() * 10);
      const minute = Math.floor(Math.random() * 60);
      const createdAt = utcDate(
        day.getUTCFullYear(),
        day.getUTCMonth() + 1,
        day.getUTCDate(),
        hour,
        minute,
      );

      const status = finalStatus(ageDays);
      const content = pick(CONTENT_CATS);
      const size = pick(SIZE_CATS);
      const weight = Number((0.3 + Math.random() * 12).toFixed(2));
      const declared = Math.round(500 + Math.random() * 45000);
      const price = Math.round(120 + weight * 45 + Math.random() * 200);
      const paymentMode: payment_mode_enum = Math.random() > 0.35 ? 'before' : 'after';
      const paymentMethod: payment_method_enum | null =
        paymentMode === 'before' ? (Math.random() > 0.4 ? 'cash' : 'chapa') : null;
      const paid =
        paymentMode === 'before' ||
        (status === 'delivered' && Math.random() > 0.25);
      const paymentStatus: payment_status_enum = paid ? 'paid' : 'pending';

      const parcelId = randomUUID();
      const tracking = `${MOCK_PREFIX}${String(seq).padStart(7, '0')}`;

      parcelBatch.push({
        id: parcelId,
        tracking_code: tracking,
        origin_branch_id: origin.id,
        destination_branch_id: dest.id,
        sender_id: senderId,
        receiver_name: faker.person.fullName(),
        receiver_phone: `+2519${String(Math.floor(Math.random() * 90000000) + 10000000)}`,
        description: `${content} — ${faker.commerce.productName()}`,
        weight_kg: weight,
        declared_value: declared,
        price,
        payment_mode: paymentMode,
        payment_method: paymentMethod,
        payment_status: paymentStatus,
        status,
        content_category: content,
        size_category: size,
        length_cm: 20 + Math.random() * 40,
        width_cm: 15 + Math.random() * 30,
        height_cm: 5 + Math.random() * 25,
        chargeable_weight_kg: weight,
        created_by: admin.id,
        created_at: createdAt,
        updated_at: new Date(createdAt.getTime() + ageDays * 3600_000),
        promised_delivery_at: addDays(createdAt, 3 + Math.floor(Math.random() * 5)),
      });

      historyBatch.push(
        ...historyForStatus(status, createdAt, admin.id, origin.id, parcelId),
      );

      if (paymentStatus === 'paid' && paymentMethod) {
        paymentBatch.push({
          id: randomUUID(),
          parcel_id: parcelId,
          amount: price,
          method: paymentMethod,
          chapa_tx_ref:
            paymentMethod === 'chapa' ? `MOCK-${tracking.replace(/-/g, '')}` : null,
          status: 'paid',
          collected_by: admin.id,
          verified_at: new Date(createdAt.getTime() + 3600_000),
          created_at: new Date(createdAt.getTime() + 1800_000),
        });
      }

      totalParcels += 1;
      if (parcelBatch.length >= BATCH) await flush();
    }
  }

  await flush();

  console.log(`Done. Created ${totalParcels} mock parcels (${MOCK_PREFIX}*).`);
  console.log('Open the dashboard and use the date filter to explore historical data.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
