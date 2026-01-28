<template>
  <div class="page">
    <!-- 顶部标题 + 统计 -->
    <div class="page-header">
      <div>
        <h2>商品管理</h2>
        <p class="sub-title">管理商品信息、价格与库存。</p>
      </div>
      <el-button type="primary" @click="openAddDialog">新增商品</el-button>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="label">商品总数</div>
          <div class="value">{{ stats.totalProducts }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="label">库存总量</div>
          <div class="value">{{ stats.totalStock }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="label">上架商品数</div>
          <div class="value">{{ stats.onlineProducts }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-input
          v-model="keyword"
          placeholder="按名称 / 类别搜索"
          clearable
          style="width: 260px"
          @keyup.enter="loadProducts"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          style="width: 150px"
        >
          <el-option label="上架" value="上架" />
          <el-option label="下架" value="下架" />
        </el-select>

        <el-button type="primary" @click="loadProducts">查询</el-button>
        <el-button @click="resetFilter">重置</el-button>
      </div>
    </el-card>

    <!-- 商品列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="products"
        border
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="category" label="类别" width="120" />
        <el-table-column prop="price" label="价格（元）" width="120">
          <template #default="{ row }">
            ¥ {{ formatPrice(row.price) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === '上架' ? 'success' : 'info'"
              effect="light"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="created_at" label="创建时间" width="180" />

        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>

            <el-divider direction="vertical" />

            <el-button
              link
              type="warning"
              size="small"
              @click="toggleStatus(row)"
            >
              {{ row.status === '上架' ? '下架' : '上架' }}
            </el-button>

            <el-divider direction="vertical" />

            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !products.length" class="empty-text">
        暂无商品，请点击右上角「新增商品」创建。
      </div>
    </el-card>

    <!-- 新增 / 编辑 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑商品' : '新增商品'"
      width="480px"
    >
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入商品名称" />
        </el-form-item>

        <el-form-item label="类别">
          <el-input v-model="form.category" placeholder="如：饮料、器材" />
        </el-form-item>

        <el-form-item label="价格">
          <el-input-number
            v-model="form.price"
            :min="0"
            :step="1"
            :precision="2"
          />
        </el-form-item>

        <el-form-item label="库存">
          <el-input-number v-model="form.stock" :min="0" :step="1" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="可填写品牌、规格等信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">
            确 定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import http from "../utils/http";

interface Product {
  id: number;
  name: string;
  category: string | null;
  price: number;
  stock: number;
  status: string; // 上架 | 下架
  remark: string | null;
  created_at: string;
}

interface ProductForm {
  name: string;
  category: string;
  price: number;
  stock: number;
  remark: string;
}

const products = ref<Product[]>([]);
const loading = ref(false);

const keyword = ref("");
const statusFilter = ref<string | null>(null);

const dialogVisible = ref(false);
const isEdit = ref(false);
const editingId = ref<number | null>(null);
const saving = ref(false);

const form = ref<ProductForm>({
  name: "",
  category: "",
  price: 0,
  stock: 0,
  remark: "",
});

// 统计信息
const stats = computed(() => {
  const totalProducts = products.value.length;
  const totalStock = products.value.reduce((sum, p) => sum + (p.stock || 0), 0);
  const onlineProducts = products.value.filter(
    (p) => p.status === "上架"
  ).length;

  return {
    totalProducts,
    totalStock,
    onlineProducts,
  };
});

const formatPrice = (v: unknown) => {
  const n = Number(v);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

// 加载列表
const loadProducts = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (keyword.value) params.keyword = keyword.value;
    if (statusFilter.value) params.status = statusFilter.value;

    const res = await http.get<Product[]>("/products", { params });
    products.value = res.data || [];
  } catch (err) {
    console.error(err);
    ElMessage.error("获取商品列表失败");
  } finally {
    loading.value = false;
  }
};

const resetFilter = () => {
  keyword.value = "";
  statusFilter.value = null;
  loadProducts();
};

// 打开新增弹窗
const openAddDialog = () => {
  isEdit.value = false;
  editingId.value = null;
  form.value = {
    name: "",
    category: "",
    price: 0,
    stock: 0,
    remark: "",
  };
  dialogVisible.value = true;
};

// 打开编辑弹窗
const openEditDialog = (row: Product) => {
  isEdit.value = true;
  editingId.value = row.id;
  form.value = {
    name: row.name,
    category: row.category || "",
    price: row.price,
    stock: row.stock,
    remark: row.remark || "",
  };
  dialogVisible.value = true;
};

// 提交表单
const submitForm = async () => {
  if (!form.value.name) {
    ElMessage.warning("请填写商品名称");
    return;
  }
  if (form.value.price < 0) {
    ElMessage.warning("价格不能为负数");
    return;
  }
  if (form.value.stock < 0) {
    ElMessage.warning("库存不能为负数");
    return;
  }

  const payload = {
    name: form.value.name,
    category: form.value.category,
    price: form.value.price,
    stock: form.value.stock,
    remark: form.value.remark,
  };

  try {
    saving.value = true;
    if (isEdit.value && editingId.value != null) {
      await http.put(`/products/${editingId.value}`, payload);
      ElMessage.success("编辑成功");
    } else {
      await http.post("/products", payload);
      ElMessage.success("新增成功");
    }

    dialogVisible.value = false;
    await loadProducts();
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "保存失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    saving.value = false;
  }
};

// 上下架
const toggleStatus = async (row: Product) => {
  const targetStatus = row.status === "上架" ? "下架" : "上架";
  try {
    await http.put(`/products/${row.id}/status`, { status: targetStatus });
    ElMessage.success("状态已更新");
    await loadProducts();
  } catch (err) {
    console.error(err);
    ElMessage.error("更新状态失败");
  }
};

// 删除
const handleDelete = (row: Product) => {
  ElMessageBox.confirm(
    `确定要删除商品「${row.name}」吗？`,
    "删除确认",
    {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    }
  )
    .then(async () => {
      try {
        await http.delete(`/products/${row.id}`);
        ElMessage.success("删除成功");
        await loadProducts();
      } catch (err) {
        console.error(err);
        ElMessage.error("删除失败，请稍后重试");
      }
    })
    .catch(() => {
      /* 用户取消 */
    });
};

onMounted(() => {
  loadProducts();
});
</script>

<style scoped>
.page {
  padding: 16px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #F2F2F7;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sub-title {
  margin: 4px 0 0;
  font-size: 13px;
  color: #86868B;
}

.stat-row {
  margin-bottom: 8px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.stat-card .label {
  font-size: 13px;
  color: #86868B;
}

.stat-card .value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 600;
  color: #1D1D1F;
}

.filter-card,
.table-card {
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.empty-text {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: #86868B;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
