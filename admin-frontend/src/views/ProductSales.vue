<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>商品售卖 / 收银台</h2>
        <p class="sub-title">快速完成商品结算，支持现金或会员余额支付，自动记录库存与会员消费</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="pos-card" shadow="hover">
          <div class="pos-title">结算面板</div>
          <el-form :model="form" label-width="80px">
            <el-form-item label="商品">
              <el-select v-model="form.product_id" placeholder="选择商品" filterable style="width: 100%">
                <el-option
                  v-for="p in productOptions"
                  :key="p.id"
                  :label="`${p.name}（¥${formatPrice(p.price)}，库存${p.stock}）`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="数量">
              <el-input-number v-model="form.quantity" :min="1" :step="1" style="width: 160px" />
            </el-form-item>

            <el-form-item label="会员">
              <el-select
                v-model="form.member_id"
                placeholder="可选，散客可留空"
                clearable
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="m in memberOptions"
                  :key="m.id"
                  :label="`${m.name}（${m.phone}，余额¥${formatPrice(m.balance)}）`"
                  :value="m.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="支付方式">
              <el-select v-model="form.pay_method" style="width: 160px">
                <el-option label="现金" value="现金" />
                <el-option label="会员余额" value="会员余额" />
              </el-select>
              <div v-if="form.pay_method === '会员余额'" class="pay-tip">需选择会员，并保证余额 ≥ 合计金额</div>
            </el-form-item>

            <el-form-item label="合计">
              <div class="amount-box">
                <div class="amount-main">¥ {{ formatPrice(totalAmount) }}</div>
                <div class="amount-sub" v-if="selectedProduct">
                  单价 ¥{{ formatPrice(selectedProduct.price) }} × 数量 {{ form.quantity || 0 }}
                </div>
              </div>
            </el-form-item>

            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可填写特殊说明或流水备注" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="saving" @click="submitSale" :disabled="!canCreate">立即结算</el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="table-card" shadow="hover">
          <div class="table-header">
            <div class="table-title">最近销售记录</div>
            <el-button type="text" @click="loadSales">刷新</el-button>
          </div>

          <el-table :data="sales" border style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="编号" width="80" />
            <el-table-column prop="product_name" label="商品" width="160" />
            <el-table-column prop="member_name" label="会员" width="140">
              <template #default="{ row }">
                <span v-if="row.member_name">{{ row.member_name }}</span>
                <span v-else class="text-muted">散客</span>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="unit_price" label="单价(元)" width="110">
              <template #default="{ row }">
                ¥ {{ formatPrice(row.unit_price) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_price" label="金额(元)" width="120">
              <template #default="{ row }">
                <span class="money">¥ {{ formatPrice(row.total_price) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="pay_method" label="支付方式" width="100" />
            <el-table-column prop="remark" label="备注" />
            <el-table-column prop="created_at" label="时间" width="180" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" size="small" :disabled="!canRefund" @click="handleRefund(row)">
                  退款
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="!loading && !sales.length" class="empty-text">暂无销售记录</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "../utils/http";
import { hasAction } from "@/utils/permission";

interface ProductOption {
  id: number;
  name: string;
  price: number;
  stock: number;
}

interface MemberOption {
  id: number;
  name: string;
  phone: string;
  balance: number;
}

interface SaleRecord {
  id: number;
  product_id: number;
  product_name: string;
  member_id: number | null;
  member_name: string | null;
  quantity: number;
  unit_price: number | string;
  total_price: number | string;
  pay_method: string;
  remark: string | null;
  created_at: string;
}

interface SaleForm {
  product_id: number | null;
  member_id: number | null;
  quantity: number;
  pay_method: string;
  remark: string;
}

const loading = ref(false);
const saving = ref(false);

const productOptions = ref<ProductOption[]>([]);
const memberOptions = ref<MemberOption[]>([]);
const sales = ref<SaleRecord[]>([]);

const form = ref<SaleForm>({
  product_id: null,
  member_id: null,
  quantity: 1,
  pay_method: "现金",
  remark: "",
});

const canCreate = hasAction("product_sale.create");
const canRefund = hasAction("product_sale.refund");

const formatPrice = (v: unknown) => {
  const n = Number(v);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

const selectedProduct = computed(() =>
  productOptions.value.find((p) => p.id === form.value.product_id) || null
);

const totalAmount = computed(() => {
  if (!selectedProduct.value) return 0;
  const qty = form.value.quantity || 0;
  return selectedProduct.value.price * qty;
});

const loadProducts = async () => {
  try {
    const res = await http.get<any[]>("/products", { params: { status: "上架" } });
    productOptions.value = (res.data || []).map((p: any) => ({
      id: p.id,
      name: p.name,
      price: p.price,
      stock: p.stock,
    }));
  } catch (err) {
    console.error(err);
    ElMessage.error("获取商品列表失败");
  }
};

const loadMembers = async () => {
  try {
    const res = await http.get<any[]>("/members");
    memberOptions.value = (res.data || []).map((m: any) => ({
      id: m.id,
      name: m.name,
      phone: m.phone,
      balance: m.balance ?? 0,
    }));
  } catch (err) {
    console.error(err);
    ElMessage.error("获取会员列表失败");
  }
};

const loadSales = async () => {
  loading.value = true;
  try {
    const res = await http.get<SaleRecord[]>("/product-sales");
    sales.value = res.data || [];
  } catch (err) {
    console.error(err);
    ElMessage.error("获取销售记录失败");
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.value = { product_id: null, member_id: null, quantity: 1, pay_method: "现金", remark: "" };
};

const submitSale = async () => {
  if (!canCreate) {
    ElMessage.warning("无收银权限");
    return;
  }
  if (!form.value.product_id) {
    ElMessage.warning("请选择商品");
    return;
  }
  if (form.value.pay_method === "会员余额" && !form.value.member_id) {
    ElMessage.warning("请选择会员后再用余额支付");
    return;
  }
  try {
    saving.value = true;
    await http.post("/product-sales", form.value);
    ElMessage.success("结算完成");
    resetForm();
    loadProducts();
    loadSales();
  } catch (err: any) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "结算失败");
  } finally {
    saving.value = false;
  }
};

const handleRefund = async (row: SaleRecord) => {
  if (!canRefund) {
    ElMessage.warning("无退款权限");
    return;
  }
  try {
    await ElMessageBox.confirm(`确认对销售 #${row.id} 发起退款吗？`, "提示", {
      type: "warning",
      confirmButtonText: "确认退款",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  try {
    await http.post(`/product-sales/${row.id}/refund`, {});
    ElMessage.success("退款成功");
    loadSales();
    loadMembers();
  } catch (err: any) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "退款失败");
  }
};

onMounted(() => {
  loadProducts();
  loadMembers();
  loadSales();
});
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sub-title {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}
.pos-card {
  border-radius: 12px;
}
.table-card {
  border-radius: 12px;
}
.pos-title {
  font-weight: 600;
  margin-bottom: 10px;
}
.amount-box {
  display: flex;
  flex-direction: column;
}
.amount-main {
  font-size: 22px;
  font-weight: 600;
}
.amount-sub {
  color: #6b7280;
  font-size: 12px;
}
.pay-tip {
  margin-left: 8px;
  color: #ea580c;
  font-size: 12px;
}
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.table-title {
  font-weight: 600;
}
.empty-text {
  text-align: center;
  color: #94a3b8;
  padding: 12px;
}
.text-muted {
  color: #9ca3af;
}
.money {
  color: #0ea5e9;
  font-weight: 600;
}
</style>
